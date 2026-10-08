from django.contrib import admin

from .models import Job, JobAttachment, JobMaterial, JobUpdate


class UpdateInline(admin.TabularInline):
    model = JobUpdate
    extra = 0
    readonly_fields = ("user", "old_status", "new_status", "comment", "created_at")


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "customer", "assigned_to", "status", "priority", "scheduled_date")
    list_filter = ("status", "priority")
    search_fields = ("title", "customer__name")
    inlines = [UpdateInline]


admin.site.register(JobAttachment)
admin.site.register(JobMaterial)
