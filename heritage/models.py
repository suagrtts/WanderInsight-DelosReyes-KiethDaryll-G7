from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Lower
from django.utils.text import slugify


class District(models.Model):
    """Geographic district or heritage corridor in Cebu (SDD ERD reference entity)."""

    class Zone(models.TextChoices):
        METRO_CEBU = "METRO_CEBU", "Metro Cebu Corridor"
        MACTAN_ISLANDS = "MACTAN_ISLANDS", "Mactan & Offshore Islands"
        NORTH_CEBU = "NORTH_CEBU", "Northern Cebu"
        SOUTH_CEBU = "SOUTH_CEBU", "Southern Cebu"

    name = models.CharField(max_length=100, unique=True)
    zone = models.CharField(max_length=30, choices=Zone.choices, default=Zone.METRO_CEBU)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "heritage_districts"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.get_zone_display()})"


class HeritageCategory(models.Model):
    """Classification of cultural landmarks (e.g., Colonial Church, Watchtower, Museum)."""

    code = models.CharField(max_length=24, unique=True)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "heritage_categories"
        verbose_name = "heritage category"
        verbose_name_plural = "heritage categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class PreservationTag(models.Model):
    """Conservation designation or visitor accessibility attribute (ManyToMany on HeritageSite)."""

    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = "heritage_preservation_tags"
        ordering = ["name"]

    def __str__(self):
        return self.name


class HeritageSite(models.Model):
    """Core cultural heritage landmark record managed by Curators and Administrators (SDD F-02)."""

    class PreservationStatus(models.TextChoices):
        WELL_PRESERVED = "WELL_PRESERVED", "Well Preserved"
        RESTORATION_ONGOING = "RESTORATION_ONGOING", "Active Restoration"
        AT_RISK = "AT_RISK", "Conservation Priority"
        ARCHIVED = "ARCHIVED", "Archived / Restricted"

    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    district = models.ForeignKey(
        District,
        on_delete=models.PROTECT,
        related_name="sites",
    )
    category = models.ForeignKey(
        HeritageCategory,
        on_delete=models.PROTECT,
        related_name="sites",
    )
    preservation_tags = models.ManyToManyField(
        PreservationTag,
        blank=True,
        related_name="sites",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="heritage_sites",
    )
    municipality = models.CharField(
        max_length=120,
        help_text="City or municipality (e.g., Cebu City, Lapu-Lapu City, Boljoon).",
    )
    established_year = models.PositiveIntegerField(
        validators=[MinValueValidator(1500), MaxValueValidator(2100)],
        help_text="Historical year founded or built (1500 to present).",
    )
    latitude = models.DecimalField(
        max_digits=8,
        decimal_places=5,
        validators=[MinValueValidator(Decimal("9.30000")), MaxValueValidator(Decimal("11.60000"))],
        help_text="Cebu latitude in decimal degrees (9.30000 to 11.60000 °N).",
    )
    longitude = models.DecimalField(
        max_digits=8,
        decimal_places=5,
        validators=[MinValueValidator(Decimal("123.20000")), MaxValueValidator(Decimal("124.70000"))],
        help_text="Cebu longitude in decimal degrees (123.20000 to 124.70000 °E).",
    )
    preservation_status = models.CharField(
        max_length=30,
        choices=PreservationStatus.choices,
        default=PreservationStatus.WELL_PRESERVED,
    )
    daily_capacity = models.PositiveIntegerField(
        default=500,
        validators=[MinValueValidator(10), MaxValueValidator(50000)],
        help_text="Recommended maximum daily visitors (10 to 50,000).",
    )
    entry_fee = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Standard admission fee in PHP (0.00 if free public access).",
    )
    custodian_organization = models.CharField(
        max_length=150,
        blank=True,
        help_text="Managing museum office, parish, or LGU heritage council.",
    )
    historical_overview = models.TextField(
        help_text="Historical background, architectural notes, and cultural significance (min. 30 characters).",
    )
    is_published = models.BooleanField(
        default=True,
        help_text="Published landmarks appear in the read-only Viewer catalog.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "heritage_sites"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                "district",
                name="uniq_heritage_site_name_district",
            ),
        ]

    def _generate_unique_slug(self):
        base_slug = slugify(self.name)[:160] or "heritage-site"
        candidate = base_slug
        counter = 2
        qs = HeritageSite.objects.exclude(pk=self.pk)
        while qs.filter(slug=candidate).exists():
            candidate = f"{base_slug}-{counter}"
            counter += 1
        return candidate

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)

    def can_manage(self, user):
        """Only the Curator who created the site or an Administrator may edit/delete it (BR-10)."""
        if not user or not user.is_authenticated:
            return False
        return bool(user.is_admin_role or self.created_by_id == user.id)

    def __str__(self):
        return f"{self.name} ({self.municipality})"


class VisitationLog(models.Model):
    """Daily visitor attendance and demographic breakdown per landmark (SDD F-03, BR-01, BR-04)."""

    class WeatherCondition(models.TextChoices):
        SUNNY = "SUNNY", "Sunny / Clear"
        PARTLY_CLOUDY = "PARTLY_CLOUDY", "Partly Cloudy"
        OVERCAST = "OVERCAST", "Overcast"
        RAINY = "RAINY", "Rainy / Monsoon"

    site = models.ForeignKey(
        HeritageSite,
        on_delete=models.CASCADE,
        related_name="visitation_logs",
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recorded_visitation_logs",
    )
    visit_date = models.DateField(
        help_text="Date of recorded foot traffic (one unique log per landmark per day, BR-04).",
    )
    local_visitors = models.PositiveIntegerField(
        default=0,
        help_text="Cebu local residents.",
    )
    domestic_visitors = models.PositiveIntegerField(
        default=0,
        help_text="Visitors from other Philippine provinces.",
    )
    foreign_visitors = models.PositiveIntegerField(
        default=0,
        help_text="International tourists.",
    )
    total_visitors = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Must equal Local + Domestic + Foreign visitors (BR-01).",
    )
    weather_condition = models.CharField(
        max_length=20,
        choices=WeatherCondition.choices,
        default=WeatherCondition.SUNNY,
    )
    special_event = models.CharField(
        max_length=120,
        blank=True,
        help_text="Optional festival, school tour, or cultural event.",
    )
    remarks = models.TextField(
        blank=True,
        help_text="Optional conservation or crowd-flow observations.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "visitation_logs"
        ordering = ["-visit_date", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["site", "visit_date"],
                name="uniq_visitation_site_date",
            ),
            models.CheckConstraint(
                condition=Q(total_visitors__gt=0),
                name="chk_visitation_total_positive",
            ),
            models.CheckConstraint(
                condition=Q(
                    total_visitors=F("local_visitors")
                    + F("domestic_visitors")
                    + F("foreign_visitors")
                ),
                name="chk_visitation_br01_origin_sum",
            ),
        ]

    def can_manage(self, user):
        """Curators can only modify logs they recorded on their own sites; Admins can manage all."""
        if not user or not user.is_authenticated:
            return False
        if user.is_admin_role:
            return True
        return bool(
            user.is_curator
            and (self.recorded_by_id == user.id or self.site.created_by_id == user.id)
        )

    def __str__(self):
        return f"{self.site.name} · {self.visit_date} ({self.total_visitors} visitors)"
