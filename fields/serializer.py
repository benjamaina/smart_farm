from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Field, FieldUpdate, UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["role"]


class UserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source="profile.role", read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "role"]


class CreateAgentSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "password", "first_name", "last_name", "email"]

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            email=validated_data.get("email", ""),
        )
        UserProfile.objects.create(user=user, role=UserProfile.ROLE_AGENT)
        return user


class FieldUpdateSerializer(serializers.ModelSerializer):
    agent_name = serializers.CharField(source="agent.get_full_name", read_only=True)
    stage_display = serializers.CharField(source="get_stage_display", read_only=True)

    class Meta:
        model = FieldUpdate
        fields = ["id", "stage", "stage_display", "notes", "agent_name", "created_at"]
        read_only_fields = ["agent_name", "created_at"]


class FieldSerializer(serializers.ModelSerializer):
    status = serializers.CharField(read_only=True)
    status_display = serializers.CharField(read_only=True)
    stage_display = serializers.CharField(source="get_stage_display", read_only=True)
    assigned_to_name = serializers.CharField(source="assigned_to.get_full_name", read_only=True)
    days_since_planting = serializers.IntegerField(read_only=True)
    updates = FieldUpdateSerializer(many=True, read_only=True)

    class Meta:
        model = Field
        fields = [
            "id", "name", "crop_type", "planting_date", "stage", "stage_display",
            "status", "status_display", "assigned_to", "assigned_to_name",
            "notes", "days_since_planting", "updates", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]