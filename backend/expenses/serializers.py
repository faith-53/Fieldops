from rest_framework import serializers

from .models import Expense


class ExpenseSerializer(serializers.ModelSerializer):
    submitted_by_name = serializers.CharField(source="submitted_by.name", read_only=True, default="")
    job_title = serializers.CharField(source="job.title", read_only=True)

    class Meta:
        model = Expense
        fields = (
            "id",
            "job",
            "job_title",
            "submitted_by",
            "submitted_by_name",
            "amount",
            "category",
            "description",
            "receipt",
            "created_at",
        )
        read_only_fields = ("submitted_by", "created_at")
