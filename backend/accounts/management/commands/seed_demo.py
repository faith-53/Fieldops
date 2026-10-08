from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Role, Skill
from customers.models import Customer
from expenses.models import Expense
from jobs.models import Job, JobPriority, JobStatus, JobUpdate
from notifications.models import Notification, NotificationKind

User = get_user_model()


class Command(BaseCommand):
    help = "Load demo FieldOps data for local development"

    def handle(self, *args, **options):
        electrical, _ = Skill.objects.get_or_create(name="Electrical")
        hvac, _ = Skill.objects.get_or_create(name="HVAC")
        plumbing, _ = Skill.objects.get_or_create(name="Plumbing")

        admin, _ = User.objects.get_or_create(
            email="admin@fieldops.local",
            defaults={"name": "Amina Otieno", "role": Role.ADMIN, "is_staff": True, "is_superuser": True},
        )
        admin.set_password("admin12345")
        admin.save()

        manager, _ = User.objects.get_or_create(
            email="manager@fieldops.local",
            defaults={"name": "David Mwangi", "role": Role.MANAGER},
        )
        manager.set_password("manager12345")
        manager.save()

        john, _ = User.objects.get_or_create(
            email="john@fieldops.local",
            defaults={
                "name": "John Kamau",
                "role": Role.TECHNICIAN,
                "latitude": Decimal("-1.268000"),
                "longitude": Decimal("36.811000"),
            },
        )
        john.set_password("tech12345")
        john.save()
        john.skills.set([electrical, hvac])

        mary, _ = User.objects.get_or_create(
            email="mary@fieldops.local",
            defaults={
                "name": "Mary Wanjiku",
                "role": Role.TECHNICIAN,
                "latitude": Decimal("-1.292000"),
                "longitude": Decimal("36.822000"),
            },
        )
        mary.set_password("tech12345")
        mary.save()
        mary.skills.set([electrical])

        brian, _ = User.objects.get_or_create(
            email="brian@fieldops.local",
            defaults={
                "name": "Brian Ochieng",
                "role": Role.TECHNICIAN,
                "latitude": Decimal("-1.303000"),
                "longitude": Decimal("36.780000"),
            },
        )
        brian.set_password("tech12345")
        brian.save()
        brian.skills.set([hvac, plumbing])

        abc, _ = Customer.objects.get_or_create(
            name="ABC Ltd",
            defaults={
                "phone": "+254711000111",
                "email": "ops@abc.example",
                "address": "Westlands, Nairobi",
                "latitude": Decimal("-1.267500"),
                "longitude": Decimal("36.810800"),
            },
        )
        kplc, _ = Customer.objects.get_or_create(
            name="Ridgeview Apartments",
            defaults={
                "phone": "+254722000222",
                "email": "fm@ridgeview.example",
                "address": "Kilimani, Nairobi",
                "latitude": Decimal("-1.292100"),
                "longitude": Decimal("36.783000"),
            },
        )
        cafe, _ = Customer.objects.get_or_create(
            name="Savanna Cafe",
            defaults={
                "phone": "+254733000333",
                "email": "hello@savanna.example",
                "address": "Karen, Nairobi",
                "latitude": Decimal("-1.319000"),
                "longitude": Decimal("36.715000"),
            },
        )

        today = timezone.localdate()
        specs = [
            ("Repair AC - Westlands", abc, john, JobStatus.IN_PROGRESS, JobPriority.HIGH, today, hvac, 18500),
            ("Install circuit breaker", abc, mary, JobStatus.ASSIGNED, JobPriority.HIGH, today + timedelta(days=1), electrical, 9200),
            ("Boiler service", kplc, brian, JobStatus.ACCEPTED, JobPriority.MEDIUM, today, plumbing, 14000),
            ("Emergency leak", cafe, None, JobStatus.PENDING, JobPriority.URGENT, today, plumbing, 7600),
            ("Quarterly HVAC check", kplc, john, JobStatus.COMPLETED, JobPriority.LOW, today - timedelta(days=1), hvac, 22000),
            ("Lighting retrofit", abc, mary, JobStatus.VERIFIED, JobPriority.MEDIUM, today - timedelta(days=3), electrical, 41000),
            ("Filter replacement", cafe, brian, JobStatus.CLOSED, JobPriority.LOW, today - timedelta(days=8), hvac, 4500),
            ("Overdue generator inspect", kplc, john, JobStatus.ASSIGNED, JobPriority.HIGH, today - timedelta(days=2), electrical, 16000),
        ]

        Job.objects.all().delete()
        Expense.objects.all().delete()
        Notification.objects.all().delete()

        for title, customer, tech, status, priority, due, skill, cost in specs:
            job = Job.objects.create(
                customer=customer,
                assigned_to=tech,
                created_by=manager,
                required_skill=skill,
                title=title,
                description=f"Field visit for {title.lower()} at {customer.address}.",
                location=customer.address,
                priority=priority,
                status=status,
                scheduled_date=due,
                estimated_cost=cost,
                actual_cost=cost - 800 if status in (JobStatus.COMPLETED, JobStatus.VERIFIED, JobStatus.CLOSED) else 0,
                completion_note="Work completed and customer signed off."
                if status in (JobStatus.COMPLETED, JobStatus.VERIFIED, JobStatus.CLOSED)
                else "",
                completed_at=timezone.now() - timedelta(hours=6)
                if status in (JobStatus.COMPLETED, JobStatus.VERIFIED, JobStatus.CLOSED)
                else None,
            )
            JobUpdate.objects.create(
                job=job,
                user=manager,
                old_status="",
                new_status=status,
                comment="Seeded workflow state",
            )
            if tech:
                Expense.objects.create(
                    job=job,
                    submitted_by=tech,
                    amount=Decimal("1200.00"),
                    category="TRANSPORT",
                    description="Matatu / fuel to site",
                )

        Notification.objects.create(
            user=john,
            title="Job # is due tomorrow",
            message="Install circuit breaker for ABC Ltd is scheduled tomorrow.",
            kind=NotificationKind.DEADLINE,
        )
        Notification.objects.create(
            user=manager,
            title="Job was completed",
            message="Quarterly HVAC check was completed.",
            kind=NotificationKind.COMPLETED,
        )
        Notification.objects.create(
            user=john,
            title="You have 1 overdue job",
            message="Generator inspect is past its scheduled date.",
            kind=NotificationKind.OVERDUE,
        )

        self.stdout.write(self.style.SUCCESS("Demo data ready."))
        self.stdout.write("Admin     admin@fieldops.local / admin12345")
        self.stdout.write("Manager   manager@fieldops.local / manager12345")
        self.stdout.write("Tech      john@fieldops.local / tech12345")
