from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from jobs.models import Job, JobStatus
from .models import Notification, NotificationKind


OPEN = [JobStatus.PENDING, JobStatus.ASSIGNED, JobStatus.ACCEPTED, JobStatus.IN_PROGRESS]


def notify(user, title, message, kind, job=None):
    if not user:
        return
    Notification.objects.create(user=user, title=title, message=message, kind=kind, job=job)


@shared_task
def send_deadline_reminders():
    tomorrow = timezone.localdate() + timedelta(days=1)
    jobs = Job.objects.filter(scheduled_date=tomorrow, status__in=OPEN).select_related("assigned_to")
    count = 0
    for job in jobs:
        if not job.assigned_to:
            continue
        exists = Notification.objects.filter(
            user=job.assigned_to,
            job=job,
            kind=NotificationKind.DEADLINE,
            created_at__date=timezone.localdate(),
        ).exists()
        if exists:
            continue
        notify(
            job.assigned_to,
            f"Job #{job.id} is due tomorrow",
            f"{job.title} for {job.customer} is scheduled for {job.scheduled_date}.",
            NotificationKind.DEADLINE,
            job,
        )
        count += 1
    return count


@shared_task
def send_overdue_alerts():
    today = timezone.localdate()
    jobs = Job.objects.filter(scheduled_date__lt=today, status__in=OPEN).select_related("assigned_to")
    by_tech = {}
    for job in jobs:
        if not job.assigned_to_id:
            continue
        by_tech.setdefault(job.assigned_to, []).append(job)
    for tech, tech_jobs in by_tech.items():
        notify(
            tech,
            f"You have {len(tech_jobs)} overdue job{'s' if len(tech_jobs) != 1 else ''}",
            "Please update or complete overdue work: " + ", ".join(f"#{j.id}" for j in tech_jobs[:8]),
            NotificationKind.OVERDUE,
        )
    return len(by_tech)


@shared_task
def notify_job_assigned(job_id):
    job = Job.objects.select_related("assigned_to", "customer").filter(pk=job_id).first()
    if not job or not job.assigned_to:
        return
    notify(
        job.assigned_to,
        f"Job #{job.id} assigned to you",
        f"{job.title} — {job.customer.name}. Priority: {job.priority}.",
        NotificationKind.ASSIGNED,
        job,
    )


@shared_task
def notify_job_completed(job_id):
    from django.contrib.auth import get_user_model
    from accounts.models import Role

    job = Job.objects.select_related("assigned_to", "customer").filter(pk=job_id).first()
    if not job:
        return
    User = get_user_model()
    managers = User.objects.filter(role__in=[Role.ADMIN, Role.MANAGER], is_active=True)
    for manager in managers:
        notify(
            manager,
            f"Job #{job.id} was completed",
            f"{job.title} was completed by {job.assigned_to.name if job.assigned_to else 'a technician'}.",
            NotificationKind.COMPLETED,
            job,
        )
