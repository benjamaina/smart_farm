from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from django.db import transaction
from fields.models import Field, FieldUpdate, UserProfile
from fields.serializer import FieldSerializer, FieldUpdateSerializer, UserSerializer, CreateAgentSerializer


class IsAdminRole(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        profile = getattr(request.user, "profile", None)
        return profile and profile.is_admin()


class FieldListView(generics.ListCreateAPIView):
    serializer_class = FieldSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        profile = getattr(self.request.user, "profile", None)
        if profile and profile.is_admin():
            return Field.objects.select_related("assigned_to").all()
        return Field.objects.filter(assigned_to=self.request.user).select_related("assigned_to")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class FieldDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FieldSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        profile = getattr(self.request.user, "profile", None)
        if profile and profile.is_admin():
            return Field.objects.all()
        return Field.objects.filter(assigned_to=self.request.user)


class FieldUpdateCreateView(generics.CreateAPIView):
    serializer_class = FieldUpdateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        profile = getattr(self.request.user, "profile", None)
        if profile and profile.is_admin():
            field = Field.objects.get(pk=self.kwargs["pk"])
        else:
            field = Field.objects.get(pk=self.kwargs["pk"], assigned_to=self.request.user)

        with transaction.atomic():
            update = serializer.save(field=field, agent=self.request.user)
            field.stage = update.stage
            field.save()


class AgentListView(generics.ListCreateAPIView):
    permission_classes = [IsAdminRole]
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.filter(profile__role=UserProfile.ROLE_AGENT)

    def post(self, request, *args, **kwargs):
        serializer = CreateAgentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = getattr(request.user, "profile", None)

        if profile and profile.is_admin():
            fields = Field.objects.all()
        else:
            fields = Field.objects.filter(assigned_to=request.user)

        fields_list = list(fields)
        data = {
            "total": len(fields_list),
            "active": sum(1 for f in fields_list if f.status == Field.STATUS_ACTIVE),
            "at_risk": sum(1 for f in fields_list if f.status == Field.STATUS_AT_RISK),
            "completed": sum(1 for f in fields_list if f.status == Field.STATUS_COMPLETED),
            "stage_breakdown": {
                "planted": sum(1 for f in fields_list if f.stage == Field.STAGE_PLANTED),
                "growing": sum(1 for f in fields_list if f.stage == Field.STAGE_GROWING),
                "ready": sum(1 for f in fields_list if f.stage == Field.STAGE_READY),
                "harvested": sum(1 for f in fields_list if f.stage == Field.STAGE_HARVESTED),
            },
        }
        return Response(data)