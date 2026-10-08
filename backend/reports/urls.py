from django.urls import path

from .views import DashboardView, JobReportView, TechnicianReportView

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("jobs/", JobReportView.as_view(), name="job-report"),
    path("technicians/", TechnicianReportView.as_view(), name="technician-report"),
]
