from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied

from .models import Expense
from .serializers import ExpenseSerializer


class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    filterset_fields = ("job", "category", "submitted_by")
    search_fields = ("description", "job__title")
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        qs = Expense.objects.select_related("job", "submitted_by")
        user = self.request.user
        if user.is_technician:
            return qs.filter(submitted_by=user)
        return qs

    def perform_create(self, serializer):
        job = serializer.validated_data["job"]
        user = self.request.user
        if user.is_technician and job.assigned_to_id != user.id:
            raise PermissionDenied("You can only record expenses on your own jobs.")
        if not user.is_manager and not user.is_technician:
            raise PermissionDenied("You cannot record expenses.")
        serializer.save(submitted_by=user)
