from django.conf import settings
from django.db import models


class JobPriority(models.TextChoices):
    LOW = "LOW", "Low"
    MEDIUM = "MEDIUM", "Medium"
    HIGH = "HIGH", "High"
    URGENT = "URGENT", "Urgent"


class JobStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    ASSIGNED = "ASSIGNED", "Assigned"
    ACCEPTED = "ACCEPTED", "Accepted"
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    COMPLETED = "COMPLETED", "Completed"
    VERIFIED = "VERIFIED", "Verified"
    CLOSED = "CLOSED", "Closed"
    CANCELLED = "CANCELLED", "Cancelled"


class AttachmentType(models.TextChoices):
    BEFORE = "BEFORE", "Before-work photo"
    AFTER = "AFTER", "After-work photo"
    RECEIPT = "RECEIPT", "Receipt"
    DOCUMENT = "DOCUMENT", "Service document"


class Job(models.Model):
    customer = models.ForeignKey("customers.Customer", on_delete=models.PROTECT, related_name="jobs")
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_jobs",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_jobs",
    )
    required_skill = models.ForeignKey(
        "accounts.Skill",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="jobs",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    priority = models.CharField(max_length=16, choices=JobPriority.choices, default=JobPriority.MEDIUM)
    status = models.CharField(max_length=20, choices=JobStatus.choices, default=JobStatus.PENDING)
    scheduled_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    actual_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    completion_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"#{self.pk} {self.title}"

    @property
    def is_overdue(self):
        from django.utils import timezone

        if not self.scheduled_date:
            return False
        if self.status in (JobStatus.COMPLETED, JobStatus.VERIFIED, JobStatus.CLOSED, JobStatus.CANCELLED):
            return False
        return self.scheduled_date < timezone.localdate()


class JobUpdate(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="updates")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    old_status = models.CharField(max_length=20, choices=JobStatus.choices, blank=True)
    new_status = models.CharField(max_length=20, choices=JobStatus.choices)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class JobAttachment(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="attachments")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    file = models.FileField(upload_to="jobs/%Y/%m/")
    kind = models.CharField(max_length=16, choices=AttachmentType.choices)
    caption = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class JobMaterial(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="materials")
    name = models.CharField(max_length=120)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    @property
    def line_total(self):
        return self.quantity * self.unit_cost
