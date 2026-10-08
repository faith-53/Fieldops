from math import atan2, cos, radians, sin, sqrt

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone

from accounts.models import Role
from config.exceptions import WorkflowError
from .models import Job, JobStatus, JobUpdate

User = get_user_model()

ALLOWED_TRANSITIONS = {
    JobStatus.PENDING: {JobStatus.ASSIGNED, JobStatus.CANCELLED},
    JobStatus.ASSIGNED: {JobStatus.ACCEPTED, JobStatus.ASSIGNED, JobStatus.PENDING, JobStatus.CANCELLED},
    JobStatus.ACCEPTED: {JobStatus.IN_PROGRESS, JobStatus.ASSIGNED, JobStatus.CANCELLED},
    JobStatus.IN_PROGRESS: {JobStatus.COMPLETED, JobStatus.CANCELLED},
    JobStatus.COMPLETED: {JobStatus.VERIFIED, JobStatus.IN_PROGRESS},
    JobStatus.VERIFIED: {JobStatus.CLOSED},
    JobStatus.CLOSED: set(),
    JobStatus.CANCELLED: set(),
}


def record_update(job, user, old_status, new_status, comment=""):
    JobUpdate.objects.create(
        job=job,
        user=user,
        old_status=old_status or "",
        new_status=new_status,
        comment=comment,
    )


def transition(job, user, new_status, comment=""):
    if new_status not in ALLOWED_TRANSITIONS.get(job.status, set()):
        raise WorkflowError(f"Cannot move a job from {job.status} to {new_status}.")
    old = job.status
    job.status = new_status
    job.save(update_fields=["status", "updated_at"])
    record_update(job, user, old, new_status, comment)
    return job


def assign_job(job, user, technician, comment=""):
    if not user.is_manager:
        raise WorkflowError("Only managers can assign jobs.", status_code=403)
    if technician.role != Role.TECHNICIAN:
        raise WorkflowError("Jobs can only be assigned to technicians.")
    if not technician.is_active:
        raise WorkflowError("Cannot assign work to an inactive technician.")
    if job.status not in (JobStatus.PENDING, JobStatus.ASSIGNED, JobStatus.ACCEPTED):
        raise WorkflowError("This job can no longer be reassigned.")
    old = job.status
    job.assigned_to = technician
    job.status = JobStatus.ASSIGNED
    job.save(update_fields=["assigned_to", "status", "updated_at"])
    record_update(job, user, old, JobStatus.ASSIGNED, comment or f"Assigned to {technician.name}")
    return job


def accept_job(job, user, comment=""):
    if job.assigned_to_id != user.id:
        raise WorkflowError("You can only accept jobs assigned to you.", status_code=403)
    if job.status != JobStatus.ASSIGNED:
        raise WorkflowError("Only assigned jobs can be accepted.")
    return transition(job, user, JobStatus.ACCEPTED, comment or "Job accepted")


def start_job(job, user, comment=""):
    if job.assigned_to_id != user.id and not user.is_manager:
        raise WorkflowError("You can only start your own jobs.", status_code=403)
    if job.status != JobStatus.ACCEPTED:
        raise WorkflowError("A job must be accepted before work can start.")
    return transition(job, user, JobStatus.IN_PROGRESS, comment or "Work started")


def complete_job(job, user, note):
    if job.assigned_to_id != user.id and not user.is_manager:
        raise WorkflowError("You can only complete your own jobs.", status_code=403)
    if job.status != JobStatus.IN_PROGRESS:
        raise WorkflowError("Only in-progress jobs can be completed.")
    if not note or not note.strip():
        raise WorkflowError("A completion note is required before marking a job complete.")
    job.completion_note = note.strip()
    job.completed_at = timezone.now()
    job.save(update_fields=["completion_note", "completed_at", "updated_at"])
    return transition(job, user, JobStatus.COMPLETED, note.strip())


def verify_job(job, user, comment=""):
    if not user.is_manager:
        raise WorkflowError("Only managers can verify completed jobs.", status_code=403)
    if job.status != JobStatus.COMPLETED:
        raise WorkflowError("Only completed jobs can be verified.")
    job.verified_at = timezone.now()
    job.save(update_fields=["verified_at", "updated_at"])
    return transition(job, user, JobStatus.VERIFIED, comment or "Work verified")


def reject_completion(job, user, comment=""):
    if not user.is_manager:
        raise WorkflowError("Only managers can send a job back to the field.", status_code=403)
    if job.status != JobStatus.COMPLETED:
        raise WorkflowError("Only completed jobs can be sent back.")
    if not comment:
        raise WorkflowError("Explain why the job is being sent back.")
    job.completed_at = None
    job.save(update_fields=["completed_at", "updated_at"])
    return transition(job, user, JobStatus.IN_PROGRESS, comment)


def close_job(job, user, comment=""):
    if not user.is_manager:
        raise WorkflowError("Only managers can close jobs.", status_code=403)
    if job.status != JobStatus.VERIFIED:
        raise WorkflowError("A job must be verified before it can be closed.")
    job.closed_at = timezone.now()
    job.save(update_fields=["closed_at", "updated_at"])
    return transition(job, user, JobStatus.CLOSED, comment or "Job closed")


def cancel_job(job, user, comment=""):
    if not user.is_manager:
        raise WorkflowError("Only managers can cancel jobs.", status_code=403)
    if job.status in (JobStatus.CLOSED, JobStatus.CANCELLED):
        raise WorkflowError("This job is already finished.")
    return transition(job, user, JobStatus.CANCELLED, comment or "Cancelled")


def add_note(job, user, comment):
    if not comment or not comment.strip():
        raise WorkflowError("Note cannot be empty.")
    record_update(job, user, job.status, job.status, comment.strip())
    return job


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371
    dlat = radians(float(lat2) - float(lat1))
    dlon = radians(float(lon2) - float(lon1))
    a = sin(dlat / 2) ** 2 + cos(radians(float(lat1))) * cos(radians(float(lat2))) * sin(dlon / 2) ** 2
    return r * 2 * atan2(sqrt(a), sqrt(1 - a))


OPEN_STATUSES = [
    JobStatus.ASSIGNED,
    JobStatus.ACCEPTED,
    JobStatus.IN_PROGRESS,
]


def suggest_technicians(job, limit=5):
    techs = (
        User.objects.filter(role=Role.TECHNICIAN, is_active=True)
        .annotate(
            current_jobs=Count("assigned_jobs", filter=Q(assigned_jobs__status__in=OPEN_STATUSES)),
        )
        .prefetch_related("skills")
    )
    customer = job.customer
    scored = []
    for tech in techs:
        skill_names = {s.name.lower() for s in tech.skills.all()}
        required = (job.required_skill.name.lower() if job.required_skill else None)
        skill_match = 40 if (required and required in skill_names) else (10 if not required else 0)
        workload = max(0, 30 - tech.current_jobs * 6)
        availability = 20 if tech.current_jobs < 4 else (5 if tech.current_jobs < 7 else 0)
        distance_km = None
        distance_score = 10
        if tech.latitude is not None and customer.latitude is not None:
            distance_km = round(
                haversine_km(tech.latitude, tech.longitude, customer.latitude, customer.longitude),
                1,
            )
            distance_score = max(0, 20 - distance_km * 2)
        score = skill_match + availability + workload + distance_score
        scored.append(
            {
                "id": tech.id,
                "name": tech.name,
                "email": tech.email,
                "skills": [s.name for s in tech.skills.all()],
                "skill_match": bool(required and required in skill_names) or not required,
                "available": tech.current_jobs < 4,
                "busy": tech.current_jobs >= 4,
                "current_jobs": tech.current_jobs,
                "distance_km": distance_km,
                "score": round(score, 1),
            }
        )
    scored.sort(key=lambda r: r["score"], reverse=True)
    return scored[:limit]
