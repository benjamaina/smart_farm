from django.db import models

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError


class UserProfile(models.Model):
    ROLE_ADMIN = "admin"
    ROLE_AGENT = "agent"
    ROLE_CHOICES = [
        (ROLE_ADMIN, "Admin"),
        (ROLE_AGENT, "Field Agent"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_AGENT)

    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    def is_agent(self):
        return self.role == self.ROLE_AGENT

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"


class Field(models.Model):
    STAGE_PLANTED = "planted"
    STAGE_GROWING = "growing"
    STAGE_READY = "ready"
    STAGE_HARVESTED = "harvested"

    STAGE_CHOICES = [
        (STAGE_PLANTED, "Planted"),
        (STAGE_GROWING, "Growing"),
        (STAGE_READY, "Ready"),
        (STAGE_HARVESTED, "Harvested"),
    ]

    STATUS_ACTIVE = "active"
    STATUS_AT_RISK = "at_risk"
    STATUS_COMPLETED = "completed"

    name = models.CharField(max_length=100, db_index=True)
    crop_type = models.CharField(max_length=100)
    planting_date = models.DateField()
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default=STAGE_PLANTED, db_index=True)
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_fields",
        db_index=True,
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_fields",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, default="")

    def clean(self):
        if not self.name:
            raise ValidationError("Field name is required")
        if not self.crop_type:
            raise ValidationError("Crop type is required")
        if self.planting_date and self.planting_date > timezone.now().date():
            raise ValidationError("Planting date cannot be in the future")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def days_since_planting(self):
        return (timezone.now().date() - self.planting_date).days

    @property
    def status(self):
        if self.stage == self.STAGE_HARVESTED:
            return self.STATUS_COMPLETED
        if self.days_since_planting > 90 and self.stage in [self.STAGE_PLANTED, self.STAGE_GROWING]:
            return self.STATUS_AT_RISK
        return self.STATUS_ACTIVE

    @property
    def status_display(self):
        mapping = {
            self.STATUS_ACTIVE: "Active",
            self.STATUS_AT_RISK: "At Risk",
            self.STATUS_COMPLETED: "Completed",
        }
        return mapping.get(self.status, "Active")

    def __str__(self):
        return f"{self.name} ({self.crop_type})"


class FieldUpdate(models.Model):
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name="updates", db_index=True)
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name="field_updates")
    stage = models.CharField(max_length=20, choices=Field.STAGE_CHOICES)
    notes = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.field.name} - {self.get_stage_display()} by {self.agent.username}"