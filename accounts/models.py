from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class User(AbstractUser):
    """Custom user for WanderInsight with a role used for RBAC (SDD F-01 / BR-10)."""

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Administrator"
        CURATOR = "CURATOR", "Curator"
        VIEWER = "VIEWER", "Viewer"

    email = models.EmailField("email address", unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.VIEWER)
    contact_number = models.CharField(
        max_length=20,
        blank=True,
        validators=[RegexValidator(r"^\+?[0-9\- ]{7,20}$", "Enter a valid contact number.")],
    )
    organization = models.CharField(
        max_length=150, blank=True, help_text="Heritage site, office, or institution."
    )
    bio = models.TextField(blank=True)
    profile_photo = models.ImageField(upload_to="profile_photos/", blank=True, null=True)

    class Meta:
        db_table = "users"

    def save(self, *args, **kwargs):
        # Superusers created via createsuperuser are always Administrators.
        if self.is_superuser:
            self.role = self.Role.ADMIN
        # Administrators can use the Django admin site for user management.
        if self.role == self.Role.ADMIN:
            self.is_staff = True
        super().save(*args, **kwargs)

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN

    @property
    def is_curator(self):
        return self.role == self.Role.CURATOR

    @property
    def is_viewer(self):
        return self.role == self.Role.VIEWER

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
