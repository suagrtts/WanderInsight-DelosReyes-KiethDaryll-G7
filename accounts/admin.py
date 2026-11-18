from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

from .models import User

admin.site.site_header = "WanderInsight Administration"
admin.site.site_title = "WanderInsight Admin"
admin.site.index_title = "Cultural Heritage Governance & Registry Console"

_default_each_context = admin.site.each_context


def _wander_each_context(request):
    context = _default_each_context(request)
    if request.user.is_authenticated and request.user.is_staff:
        context["wi_admin_stats"] = {
            "total_users": User.objects.count(),
            "admin_count": User.objects.filter(role=User.Role.ADMIN).count(),
            "curator_count": User.objects.filter(role=User.Role.CURATOR).count(),
            "viewer_count": User.objects.filter(role=User.Role.VIEWER).count(),
            "active_count": User.objects.filter(is_active=True).count(),
        }
    return context


admin.site.each_context = _wander_each_context


@admin.register(User)
class WanderUserAdmin(UserAdmin):
    list_display = ("username", "full_name_display", "email", "role_badge", "organization", "is_active")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("username", "email", "first_name", "last_name", "organization")
    ordering = ("-date_joined",)
    fieldsets = UserAdmin.fieldsets + (
        ("WanderInsight Profile", {"fields": ("role", "contact_number", "organization", "bio", "profile_photo")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("WanderInsight Profile", {"fields": ("email", "role", "organization")}),
    )

    @admin.display(description="Full Name", ordering="first_name")
    def full_name_display(self, obj):
        return obj.get_full_name() or "—"

    @admin.display(description="Role", ordering="role")
    def role_badge(self, obj):
        role_cls = (obj.role or "viewer").lower()
        return format_html(
            '<span class="badge role-badge role-{}">{}</span>',
            role_cls,
            obj.get_role_display(),
        )

