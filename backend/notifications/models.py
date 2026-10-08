from django.conf import settings
from django.db import models


class NotificationKind(models.TextChoices):
    DEADLINE = "DEADLINE", "Deadline"
    COMPLETED = "COMPLETED", "Completed"
    OVERDUE = "OVERDUE", "Overdue"
    ASSIGNED = "ASSIGNED", "Assigned"
    INFO = "INFO", "Info"


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=200)
    message = models.TextField()
    kind = models.CharField(max_length=20, choices=NotificationKind.choices, default=NotificationKind.INFO)
    job = models.ForeignKey("jobs.Job", on_delete=models.CASCADE, null=True, blank=True, related_name="notifications")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
