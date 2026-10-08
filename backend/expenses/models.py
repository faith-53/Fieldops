from django.conf import settings
from django.db import models


class ExpenseCategory(models.TextChoices):
    MATERIALS = "MATERIALS", "Materials"
    TRANSPORT = "TRANSPORT", "Transport"
    FUEL = "FUEL", "Fuel"
    TOOLS = "TOOLS", "Tools"
    OTHER = "OTHER", "Other"


class Expense(models.Model):
    job = models.ForeignKey("jobs.Job", on_delete=models.CASCADE, related_name="expenses")
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="expenses"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.CharField(max_length=20, choices=ExpenseCategory.choices, default=ExpenseCategory.OTHER)
    description = models.CharField(max_length=255)
    receipt = models.FileField(upload_to="expenses/%Y/%m/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.category} {self.amount}"
