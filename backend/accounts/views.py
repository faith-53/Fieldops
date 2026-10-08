from django.contrib.auth import get_user_model
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from jobs.models import Job, JobStatus
from .models import Skill
from .permissions import IsAdmin, IsAdminOrManager
from .serializers import (
    EmailTokenObtainPairSerializer,
    MeSerializer,
    SkillSerializer,
    UserSerializer,
)

User = get_user_model()


class LoginView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer
    permission_classes = ()


class RefreshView(TokenRefreshView):
    permission_classes = ()


class MeViewSet(viewsets.GenericViewSet):
    serializer_class = MeSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def me(self, request):
        return Response(MeSerializer(request.user).data)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.prefetch_related("skills").all()
    serializer_class = UserSerializer
    search_fields = ("name", "email")
    filterset_fields = ("role", "is_active")

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAdminOrManager()]
        return [IsAdmin()]


class SkillViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsAdminOrManager()]
        return [IsAuthenticated()]


class TechnicianPerformanceViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminOrManager]

    def list(self, request):
        techs = User.objects.filter(role="TECHNICIAN", is_active=True).prefetch_related("skills")
        rows = []
        for tech in techs:
            assigned = Job.objects.filter(assigned_to=tech)
            total = assigned.count()
            completed = assigned.filter(status__in=[JobStatus.COMPLETED, JobStatus.VERIFIED, JobStatus.CLOSED]).count()
            rate = round((completed / total) * 100, 1) if total else 0
            rows.append(
                {
                    "id": tech.id,
                    "name": tech.name,
                    "email": tech.email,
                    "jobs": total,
                    "completed": completed,
                    "rate": rate,
                    "open_jobs": assigned.exclude(
                        status__in=[JobStatus.COMPLETED, JobStatus.VERIFIED, JobStatus.CLOSED, JobStatus.CANCELLED]
                    ).count(),
                }
            )
        rows.sort(key=lambda r: r["completed"], reverse=True)
        return Response(rows)
