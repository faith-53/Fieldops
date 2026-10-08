from datetime import datetime
from decimal import Decimal
from io import BytesIO, StringIO

from django.db.models import Count, Sum
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Role
from accounts.permissions import IsAdminOrManager
from expenses.models import Expense
from jobs.models import Job, JobStatus
from django.contrib.auth import get_user_model
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

User = get_user_model()

DONE = [JobStatus.COMPLETED, JobStatus.VERIFIED, JobStatus.CLOSED]


def parse_period(request):
    start = request.query_params.get("start")
    end = request.query_params.get("end")
    today = timezone.localdate()
    if start:
        start = datetime.strptime(start, "%Y-%m-%d").date()
    else:
        start = today.replace(day=1)
    if end:
        end = datetime.strptime(end, "%Y-%m-%d").date()
    else:
        end = today
    return start, end


def jobs_in_period(start, end):
    return Job.objects.filter(created_at__date__gte=start, created_at__date__lte=end)


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()
        user = request.user
        jobs = Job.objects.all()
        if user.is_technician:
            jobs = jobs.filter(assigned_to=user)

        todays = jobs.filter(scheduled_date=today).exclude(status=JobStatus.CANCELLED)
        completed_today = jobs.filter(completed_at__date=today)
        overdue = jobs.filter(scheduled_date__lt=today).exclude(
            status__in=[JobStatus.COMPLETED, JobStatus.VERIFIED, JobStatus.CLOSED, JobStatus.CANCELLED]
        )

        expenses_qs = Expense.objects.filter(created_at__date=today)
        if user.is_technician:
            expenses_qs = expenses_qs.filter(submitted_by=user)
        expenses_today = expenses_qs.aggregate(total=Sum("amount"))["total"] or Decimal("0")
        revenue_today = completed_today.aggregate(total=Sum("estimated_cost"))["total"] or Decimal("0")

        status_counts = {
            row["status"]: row["c"]
            for row in jobs.exclude(status=JobStatus.CANCELLED).values("status").annotate(c=Count("id"))
        }

        techs = []
        if user.is_manager:
            for tech in User.objects.filter(role=Role.TECHNICIAN, is_active=True):
                assigned = Job.objects.filter(assigned_to=tech)
                total = assigned.count()
                completed = assigned.filter(status__in=DONE).count()
                techs.append(
                    {
                        "id": tech.id,
                        "name": tech.name,
                        "jobs": total,
                        "rate": round((completed / total) * 100) if total else 0,
                    }
                )
            techs.sort(key=lambda t: t["jobs"], reverse=True)

        return Response(
            {
                "today_jobs": todays.count(),
                "completed": completed_today.count(),
                "overdue": overdue.count(),
                "revenue": revenue_today,
                "expenses": expenses_today,
                "profit": revenue_today - expenses_today,
                "jobs_by_status": status_counts,
                "technician_performance": techs[:8],
            }
        )


class JobReportView(APIView):
    permission_classes = [IsAdminOrManager]

    def get(self, request):
        start, end = parse_period(request)
        jobs = jobs_in_period(start, end)
        total = jobs.count()
        completed = jobs.filter(status__in=DONE).count()
        cancelled = jobs.filter(status=JobStatus.CANCELLED).count()
        overdue = jobs.filter(scheduled_date__lt=timezone.localdate()).exclude(
            status__in=DONE + [JobStatus.CANCELLED]
        ).count()
        payload = {
            "start": start,
            "end": end,
            "total_jobs": total,
            "completed": completed,
            "cancelled": cancelled,
            "overdue": overdue,
            "completion_rate": round((completed / total) * 100, 1) if total else 0,
            "revenue": jobs.filter(status__in=DONE).aggregate(t=Sum("estimated_cost"))["t"] or 0,
            "expenses": Expense.objects.filter(created_at__date__gte=start, created_at__date__lte=end).aggregate(
                t=Sum("amount")
            )["t"]
            or 0,
        }
        fmt = request.query_params.get("format")
        if fmt == "csv":
            return csv_response(
                "job_report.csv",
                ["period_start", "period_end", "total_jobs", "completed", "cancelled", "overdue", "completion_rate"],
                [
                    [
                        payload["start"],
                        payload["end"],
                        payload["total_jobs"],
                        payload["completed"],
                        payload["cancelled"],
                        payload["overdue"],
                        payload["completion_rate"],
                    ]
                ],
            )
        if fmt == "pdf":
            return pdf_report("Job report", payload)
        return Response(payload)


class TechnicianReportView(APIView):
    permission_classes = [IsAdminOrManager]

    def get(self, request):
        start, end = parse_period(request)
        rows = []
        for tech in User.objects.filter(role=Role.TECHNICIAN, is_active=True):
            assigned = Job.objects.filter(assigned_to=tech, created_at__date__gte=start, created_at__date__lte=end)
            total = assigned.count()
            completed = assigned.filter(status__in=DONE).count()
            rows.append(
                {
                    "technician": tech.name,
                    "jobs": total,
                    "completed": completed,
                    "rate": round((completed / total) * 100, 1) if total else 0,
                }
            )
        fmt = request.query_params.get("format")
        if fmt == "csv":
            return csv_response(
                "technician_report.csv",
                ["technician", "jobs", "completed", "rate"],
                [[r["technician"], r["jobs"], r["completed"], r["rate"]] for r in rows],
            )
        if fmt == "pdf":
            return pdf_table("Technician report", ["Technician", "Jobs", "Completed", "Rate"], rows)
        return Response({"start": start, "end": end, "rows": rows})


def csv_response(filename, headers, rows):
    import csv

    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    writer.writerows(rows)
    response = HttpResponse(buffer.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def pdf_report(title, payload):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = [Paragraph(f"FieldOps — {title}", styles["Title"]), Spacer(1, 12)]
    story.append(Paragraph(f"Period: {payload['start']} – {payload['end']}", styles["Normal"]))
    data = [[k.replace("_", " ").title(), str(v)] for k, v in payload.items()]
    table = Table(data, colWidths=[220, 220])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#0f3d3e")),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("PADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(Spacer(1, 16))
    story.append(table)
    doc.build(story)
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{title.lower().replace(" ", "_")}.pdf"'
    return response


def pdf_table(title, headers, rows):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = [Paragraph(f"FieldOps — {title}", styles["Title"]), Spacer(1, 16)]
    data = [headers] + [[r["technician"], r["jobs"], r["completed"], f'{r["rate"]}%'] for r in rows]
    table = Table(data, colWidths=[160, 80, 90, 80])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f3d3e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ("PADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(table)
    doc.build(story)
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{title.lower().replace(" ", "_")}.pdf"'
    return response
