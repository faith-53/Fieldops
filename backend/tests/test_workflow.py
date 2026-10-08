import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import Role, Skill
from customers.models import Customer
from jobs.models import Job, JobPriority, JobStatus

User = get_user_model()


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def users(db):
    skill = Skill.objects.create(name="Electrical")
    manager = User.objects.create_user(
        email="mgr@example.com", password="pass12345", name="Manager", role=Role.MANAGER
    )
    tech = User.objects.create_user(
        email="tech@example.com", password="pass12345", name="John", role=Role.TECHNICIAN
    )
    other = User.objects.create_user(
        email="other@example.com", password="pass12345", name="Mary", role=Role.TECHNICIAN
    )
    tech.skills.add(skill)
    customer = Customer.objects.create(
        name="ABC Ltd", phone="0700", address="Westlands", latitude="-1.2675", longitude="36.8108"
    )
    return {"manager": manager, "tech": tech, "other": other, "customer": customer, "skill": skill}


def auth(api, user):
    api.force_authenticate(user=user)
    return api


@pytest.mark.django_db
def test_login_returns_jwt(api, users):
    res = api.post("/api/auth/login/", {"email": "mgr@example.com", "password": "pass12345"}, format="json")
    assert res.status_code == 200
    assert "access" in res.data
    assert res.data["user"]["role"] == "MANAGER"


@pytest.mark.django_db
def test_technician_cannot_list_customers(api, users):
    auth(api, users["tech"])
    res = api.get("/api/customers/")
    assert res.status_code == 403


@pytest.mark.django_db
def test_complete_requires_note(api, users):
    job = Job.objects.create(
        customer=users["customer"],
        assigned_to=users["tech"],
        created_by=users["manager"],
        title="Repair AC",
        status=JobStatus.IN_PROGRESS,
        priority=JobPriority.HIGH,
    )
    auth(api, users["tech"])
    res = api.post(f"/api/jobs/{job.id}/complete/", {"note": ""}, format="json")
    assert res.status_code == 400
    job.refresh_from_db()
    assert job.status == JobStatus.IN_PROGRESS


@pytest.mark.django_db
def test_workflow_happy_path(api, users):
    auth(api, users["manager"])
    created = api.post(
        "/api/jobs/",
        {
            "customer": users["customer"].id,
            "title": "Repair AC - Westlands",
            "description": "Unit not cooling",
            "priority": "HIGH",
            "required_skill": users["skill"].id,
            "estimated_cost": "18500.00",
        },
        format="json",
    )
    assert created.status_code == 201
    job_id = created.data["id"]
    assigned = api.post(f"/api/jobs/{job_id}/assign/", {"technician_id": users["tech"].id}, format="json")
    assert assigned.status_code == 200
    assert assigned.data["status"] == JobStatus.ASSIGNED

    auth(api, users["tech"])
    assert api.post(f"/api/jobs/{job_id}/accept/", {}, format="json").data["status"] == JobStatus.ACCEPTED
    assert api.post(f"/api/jobs/{job_id}/start/", {}, format="json").data["status"] == JobStatus.IN_PROGRESS
    done = api.post(f"/api/jobs/{job_id}/complete/", {"note": "Recharged gas and tested airflow."}, format="json")
    assert done.status_code == 200
    assert done.data["status"] == JobStatus.COMPLETED

    auth(api, users["manager"])
    assert api.post(f"/api/jobs/{job_id}/verify/", {}, format="json").data["status"] == JobStatus.VERIFIED
    assert api.post(f"/api/jobs/{job_id}/close/", {}, format="json").data["status"] == JobStatus.CLOSED


@pytest.mark.django_db
def test_technician_cannot_see_others_jobs(api, users):
    Job.objects.create(
        customer=users["customer"],
        assigned_to=users["tech"],
        title="John job",
        status=JobStatus.ASSIGNED,
    )
    Job.objects.create(
        customer=users["customer"],
        assigned_to=users["other"],
        title="Mary job",
        status=JobStatus.ASSIGNED,
    )
    auth(api, users["tech"])
    res = api.get("/api/jobs/")
    titles = [row["title"] for row in res.data["results"]]
    assert "John job" in titles
    assert "Mary job" not in titles


@pytest.mark.django_db
def test_assignment_suggestions_score_skill(api, users):
    job = Job.objects.create(
        customer=users["customer"],
        created_by=users["manager"],
        title="Panel upgrade",
        required_skill=users["skill"],
        status=JobStatus.PENDING,
    )
    auth(api, users["manager"])
    res = api.get(f"/api/jobs/{job.id}/suggestions/")
    assert res.status_code == 200
    assert res.data[0]["id"] == users["tech"].id
