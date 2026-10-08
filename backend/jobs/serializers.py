from rest_framework import serializers

from accounts.serializers import UserSerializer
from customers.serializers import CustomerSerializer
from .models import Job, JobAttachment, JobMaterial, JobUpdate


class JobUpdateSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.name", read_only=True, default="")

    class Meta:
        model = JobUpdate
        fields = ("id", "user", "user_name", "old_status", "new_status", "comment", "created_at")
        read_only_fields = fields


class JobAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source="uploaded_by.name", read_only=True, default="")

    class Meta:
        model = JobAttachment
        fields = ("id", "file", "kind", "caption", "uploaded_by", "uploaded_by_name", "created_at")
        read_only_fields = ("uploaded_by", "created_at")


class JobMaterialSerializer(serializers.ModelSerializer):
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = JobMaterial
        fields = ("id", "name", "quantity", "unit_cost", "line_total", "created_at")
        read_only_fields = ("created_at",)


class JobListSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    assigned_to_name = serializers.CharField(source="assigned_to.name", read_only=True, default=None)
    required_skill_name = serializers.CharField(source="required_skill.name", read_only=True, default=None)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Job
        fields = (
            "id",
            "title",
            "priority",
            "status",
            "scheduled_date",
            "customer",
            "customer_name",
            "assigned_to",
            "assigned_to_name",
            "required_skill",
            "required_skill_name",
            "location",
            "estimated_cost",
            "actual_cost",
            "is_overdue",
            "created_at",
        )


class JobSerializer(serializers.ModelSerializer):
    customer_detail = CustomerSerializer(source="customer", read_only=True)
    assigned_to_detail = UserSerializer(source="assigned_to", read_only=True)
    required_skill_name = serializers.CharField(source="required_skill.name", read_only=True, default=None)
    updates = JobUpdateSerializer(many=True, read_only=True)
    attachments = JobAttachmentSerializer(many=True, read_only=True)
    materials = JobMaterialSerializer(many=True, read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Job
        fields = (
            "id",
            "customer",
            "customer_detail",
            "assigned_to",
            "assigned_to_detail",
            "created_by",
            "required_skill",
            "required_skill_name",
            "title",
            "description",
            "location",
            "priority",
            "status",
            "scheduled_date",
            "completed_at",
            "verified_at",
            "closed_at",
            "estimated_cost",
            "actual_cost",
            "completion_note",
            "is_overdue",
            "created_at",
            "updated_at",
            "updates",
            "attachments",
            "materials",
        )
        read_only_fields = (
            "status",
            "assigned_to",
            "created_by",
            "completed_at",
            "verified_at",
            "closed_at",
            "created_at",
            "updated_at",
            "completion_note",
        )


class AssignSerializer(serializers.Serializer):
    technician_id = serializers.IntegerField()
    comment = serializers.CharField(required=False, allow_blank=True)


class CommentSerializer(serializers.Serializer):
    comment = serializers.CharField(required=False, allow_blank=True)


class CompleteSerializer(serializers.Serializer):
    note = serializers.CharField()
