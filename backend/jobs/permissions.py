from rest_framework.permissions import BasePermission

from .models import Job, JobAttachment, JobMaterial


class CanManageJobs(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_manager:
            return True
        if user.is_technician:
            return view.action != "create"
        return False

    def has_object_permission(self, request, view):
        user = request.user
        if user.is_manager:
            return True
        obj = view.get_object()
        job = obj if isinstance(obj, Job) else getattr(obj, "job", None)
        return bool(job and job.assigned_to_id == user.id)


def job_from_obj(obj):
    if isinstance(obj, Job):
        return obj
    if isinstance(obj, (JobAttachment, JobMaterial)):
        return obj.job
    return getattr(obj, "job", None)
