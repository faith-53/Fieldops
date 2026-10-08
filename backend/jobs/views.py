from django.contrib.auth import get_user_model
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from .models import Job, JobAttachment, JobMaterial
from .permissions import CanManageJobs
from .serializers import (
    AssignSerializer,
    CommentSerializer,
    CompleteSerializer,
    JobAttachmentSerializer,
    JobListSerializer,
    JobMaterialSerializer,
    JobSerializer,
)
from . import services
from notifications.tasks import notify_job_assigned, notify_job_completed

User = get_user_model()


def enqueue(task, *args):
    try:
        task.delay(*args)
    except Exception:
        task(*args)


class JobViewSet(viewsets.ModelViewSet):
    permission_classes = [CanManageJobs]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    search_fields = ("title", "description", "location", "customer__name")
    filterset_fields = ("status", "priority", "assigned_to", "customer")
    ordering_fields = ("created_at", "scheduled_date", "priority")

    def get_queryset(self):
        qs = (
            Job.objects.select_related("customer", "assigned_to", "required_skill", "created_by")
            .prefetch_related("updates", "attachments", "materials", "assigned_to__skills")
        )
        user = self.request.user
        if user.is_technician:
            return qs.filter(assigned_to=user)
        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return JobListSerializer
        return JobSerializer

    def perform_create(self, serializer):
        job = serializer.save(created_by=self.request.user)
        if not job.location and job.customer:
            job.location = job.customer.address
            job.save(update_fields=["location"])
        services.record_update(job, self.request.user, "", job.status, "Job created")

    def update(self, request, *args, **kwargs):
        if request.user.is_technician:
            return Response(
                {"detail": "Technicians must use workflow actions instead of editing job records."},
                status=403,
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not request.user.is_admin:
            return Response({"detail": "Jobs cannot be deleted. Cancel them instead."}, status=403)
        return super().destroy(request, *args, **kwargs)

    def _job(self):
        return self.get_object()

    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        serializer = AssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        technician = User.objects.filter(pk=serializer.validated_data["technician_id"]).first()
        if not technician:
            return Response({"detail": "Technician not found."}, status=404)
        job = services.assign_job(
            self._job(), request.user, technician, serializer.validated_data.get("comment", "")
        )
        enqueue(notify_job_assigned, job.id)
        return Response(JobSerializer(job, context=self.get_serializer_context()).data)

    @action(detail=True, methods=["get"])
    def suggestions(self, request, pk=None):
        job = self._job()
        if not request.user.is_manager:
            return Response({"detail": "Only managers can view assignment suggestions."}, status=403)
        return Response(services.suggest_technicians(job))

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        job = services.accept_job(self._job(), request.user, request.data.get("comment", ""))
        return Response(JobSerializer(job, context=self.get_serializer_context()).data)

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        job = services.start_job(self._job(), request.user, request.data.get("comment", ""))
        return Response(JobSerializer(job, context=self.get_serializer_context()).data)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        serializer = CompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job = services.complete_job(self._job(), request.user, serializer.validated_data["note"])
        enqueue(notify_job_completed, job.id)
        return Response(JobSerializer(job, context=self.get_serializer_context()).data)

    @action(detail=True, methods=["post"])
    def verify(self, request, pk=None):
        job = services.verify_job(self._job(), request.user, request.data.get("comment", ""))
        return Response(JobSerializer(job, context=self.get_serializer_context()).data)

    @action(detail=True, methods=["post"])
    def reopen(self, request, pk=None):
        serializer = CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job = services.reject_completion(self._job(), request.user, serializer.validated_data.get("comment"))
        return Response(JobSerializer(job, context=self.get_serializer_context()).data)

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        job = services.close_job(self._job(), request.user, request.data.get("comment", ""))
        return Response(JobSerializer(job, context=self.get_serializer_context()).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        job = services.cancel_job(self._job(), request.user, request.data.get("comment", ""))
        return Response(JobSerializer(job, context=self.get_serializer_context()).data)

    @action(detail=True, methods=["post"])
    def notes(self, request, pk=None):
        job = services.add_note(self._job(), request.user, request.data.get("comment", ""))
        return Response(JobSerializer(job, context=self.get_serializer_context()).data)

    @action(detail=True, methods=["post"], url_path="attachments")
    def attachments(self, request, pk=None):
        job = self._job()
        serializer = JobAttachmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(job=job, uploaded_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="materials")
    def materials(self, request, pk=None):
        job = self._job()
        serializer = JobMaterialSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        material = serializer.save(job=job)
        job.actual_cost = sum(m.line_total for m in job.materials.all())
        job.save(update_fields=["actual_cost", "updated_at"])
        return Response(JobMaterialSerializer(material).data, status=status.HTTP_201_CREATED)
