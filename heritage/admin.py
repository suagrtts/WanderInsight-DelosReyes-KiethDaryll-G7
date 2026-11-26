from django.contrib import admin

from .models import District, HeritageCategory, HeritageSite, PreservationTag


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ("name", "zone")
    list_filter = ("zone",)
    search_fields = ("name", "description")


@admin.register(HeritageCategory)
class HeritageCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code", "description")


@admin.register(PreservationTag)
class PreservationTagAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")


@admin.register(HeritageSite)
class HeritageSiteAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "municipality",
        "district",
        "category",
        "preservation_status",
        "created_by",
        "is_published",
    )
    list_filter = ("preservation_status", "is_published", "district", "category")
    search_fields = ("name", "municipality", "custodian_organization", "historical_overview")
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ("preservation_tags",)
