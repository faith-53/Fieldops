from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Skill

User = get_user_model()


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ("id", "name")


class UserSerializer(serializers.ModelSerializer):
    skills = SkillSerializer(many=True, read_only=True)
    skill_ids = serializers.PrimaryKeyRelatedField(
        source="skills", many=True, queryset=Skill.objects.all(), write_only=True, required=False
    )
    password = serializers.CharField(write_only=True, required=False, min_length=8)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "name",
            "role",
            "phone",
            "is_active",
            "skills",
            "skill_ids",
            "latitude",
            "longitude",
            "password",
            "created_at",
        )
        read_only_fields = ("created_at",)

    def create(self, validated_data):
        skills = validated_data.pop("skills", [])
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if not password:
            raise serializers.ValidationError({"password": "Password is required."})
        user.set_password(password)
        user.is_staff = user.role == "ADMIN"
        user.save()
        if skills:
            user.skills.set(skills)
        return user

    def update(self, instance, validated_data):
        skills = validated_data.pop("skills", None)
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.is_staff = instance.role == "ADMIN"
        instance.save()
        if skills is not None:
            instance.skills.set(skills)
        return instance


class MeSerializer(serializers.ModelSerializer):
    skills = SkillSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "name",
            "role",
            "phone",
            "is_active",
            "skills",
            "latitude",
            "longitude",
        )


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = User.USERNAME_FIELD

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = MeSerializer(self.user).data
        return data
