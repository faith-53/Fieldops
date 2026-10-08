from django.urls import path

from .views import TechnicianPerformanceViewSet

urlpatterns = [
    path("performance/", TechnicianPerformanceViewSet.as_view({"get": "list"}), name="technician-performance"),
]
