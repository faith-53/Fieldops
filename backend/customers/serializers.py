from rest_framework import serializers

from .models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = (
            "id",
            "name",
            "phone",
            "email",
            "address",
            "latitude",
            "longitude",
            "notes",
            "created_at",
        )
        read_only_fields = ("created_at",)
