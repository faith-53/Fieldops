from rest_framework import viewsets

from accounts.permissions import IsAdminOrManager
from .models import Customer
from .serializers import CustomerSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAdminOrManager]
    search_fields = ("name", "phone", "email", "address")
    ordering_fields = ("name", "created_at")
