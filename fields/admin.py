from django.contrib import admin

from django.contrib import admin
from .models import Field, FieldUpdate, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role")
    list_filter = ("role",)


@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    list_display = ("name", "crop_type", "stage", "assigned_to", "planting_date", "created_by")
    list_filter = ("stage",)
    search_fields = ("name", "crop_type")


@admin.register(FieldUpdate)
class FieldUpdateAdmin(admin.ModelAdmin):
    list_display = ("field", "stage", "agent", "created_at")
    list_filter = ("stage",)