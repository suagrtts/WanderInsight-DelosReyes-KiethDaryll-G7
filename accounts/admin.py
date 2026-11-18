from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class WanderUserAdmin(UserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "role", "is_active")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("username", "email", "first_name", "last_name")
    fieldsets = UserAdmin.fieldsets + (
        ("WanderInsight Profile", {"fields": ("role", "contact_number", "organization", "bio", "profile_photo")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("WanderInsight Profile", {"fields": ("email", "role")}),
    )
