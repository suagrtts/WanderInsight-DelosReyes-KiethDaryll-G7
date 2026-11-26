from decimal import Decimal

from django import forms
from django.utils import timezone

from .models import District, HeritageCategory, HeritageSite, PreservationTag, VisitationLog


class HeritageFormMixin:
    """Applies consistent Bootstrap & accessible ARIA attributes to form widgets."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.CheckboxSelectMultiple):
                widget.attrs.setdefault("class", "wi-checkbox-grid")
            elif isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", "form-select")
            else:
                widget.attrs.setdefault("class", "form-control")

        if self.is_bound:
            for name in self.errors:
                if name in self.fields:
                    self.fields[name].widget.attrs["aria-invalid"] = "true"


class HeritageSiteForm(HeritageFormMixin, forms.ModelForm):
    preservation_tags = forms.ModelMultipleChoiceField(
        queryset=PreservationTag.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Conservation Designations & Visitor Features",
        help_text="Select all official heritage markers or conservation attributes that apply.",
    )

    class Meta:
        model = HeritageSite
        fields = (
            "name",
            "district",
            "category",
            "municipality",
            "established_year",
            "preservation_status",
            "latitude",
            "longitude",
            "daily_capacity",
            "entry_fee",
            "custodian_organization",
            "preservation_tags",
            "cover_image",
            "image_url",
            "historical_overview",
            "is_published",
        )
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "e.g., Basilica Minore del Santo Niño"}),
            "municipality": forms.TextInput(attrs={"placeholder": "e.g., Cebu City"}),
            "established_year": forms.NumberInput(attrs={"min": 1500, "max": 2100}),
            "latitude": forms.NumberInput(attrs={"step": "0.00001", "placeholder": "10.29420"}),
            "longitude": forms.NumberInput(attrs={"step": "0.00001", "placeholder": "123.90210"}),
            "daily_capacity": forms.NumberInput(attrs={"min": 10, "max": 50000}),
            "entry_fee": forms.NumberInput(attrs={"step": "0.01", "min": "0.00"}),
            "custodian_organization": forms.TextInput(
                attrs={"placeholder": "e.g., Order of Saint Augustine / Cebu City Heritage Office"}
            ),
            "cover_image": forms.ClearableFileInput(),
            "image_url": forms.URLInput(
                attrs={"placeholder": "https://upload.wikimedia.org/..."}
            ),
            "historical_overview": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Describe architectural features, historical era, and current conservation state...",
                }
            ),
        }

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip()
        if len(name) < 3:
            raise forms.ValidationError("Landmark name must be at least 3 characters long.")
        return name

    def clean_municipality(self):
        municipality = (self.cleaned_data.get("municipality") or "").strip()
        if len(municipality) < 2:
            raise forms.ValidationError("Enter a valid city or municipality name.")
        return municipality

    def clean_established_year(self):
        year = self.cleaned_data.get("established_year")
        current_year = timezone.localdate().year
        if year is not None and (year < 1500 or year > current_year):
            raise forms.ValidationError(
                f"Established year must be between 1500 and {current_year}."
            )
        return year

    def clean_latitude(self):
        lat = self.cleaned_data.get("latitude")
        if lat is not None and not (Decimal("9.30000") <= lat <= Decimal("11.60000")):
            raise forms.ValidationError(
                "Latitude must fall within Cebu province bounds (9.30000°N to 11.60000°N)."
            )
        return lat

    def clean_longitude(self):
        lng = self.cleaned_data.get("longitude")
        if lng is not None and not (Decimal("123.20000") <= lng <= Decimal("124.70000")):
            raise forms.ValidationError(
                "Longitude must fall within Cebu province bounds (123.20000°E to 124.70000°E)."
            )
        return lng

    def clean_daily_capacity(self):
        cap = self.cleaned_data.get("daily_capacity")
        if cap is not None and (cap < 10 or cap > 50000):
            raise forms.ValidationError(
                "Daily conservation capacity must be between 10 and 50,000 visitors."
            )
        return cap

    def clean_entry_fee(self):
        fee = self.cleaned_data.get("entry_fee")
        if fee is not None and fee < Decimal("0.00"):
            raise forms.ValidationError("Admission fee cannot be negative.")
        return fee

    def clean_cover_image(self):
        photo = self.cleaned_data.get("cover_image")
        if photo and hasattr(photo, "size"):
            if photo.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Landmark photograph must be 5 MB or smaller.")
            content_type = getattr(photo, "content_type", None)
            if content_type and content_type not in {"image/jpeg", "image/png", "image/webp"}:
                raise forms.ValidationError("Upload a valid JPEG, PNG, or WebP photograph.")
        return photo

    def clean_historical_overview(self):
        overview = (self.cleaned_data.get("historical_overview") or "").strip()
        if len(overview) < 30:
            raise forms.ValidationError(
                "Provide a historical overview of at least 30 characters describing the landmark's significance."
            )
        return overview

    def clean(self):
        cleaned = super().clean()
        name = cleaned.get("name")
        district = cleaned.get("district")
        if name and district:
            qs = HeritageSite.objects.filter(name__iexact=name, district=district)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error(
                    "name",
                    f'A heritage site named "{name}" is already registered in {district.name}.',
                )
        return cleaned


class DistrictForm(HeritageFormMixin, forms.ModelForm):
    class Meta:
        model = District
        fields = ("name", "zone", "description")
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "e.g., Old Downtown Cebu Heritage District"}),
            "description": forms.Textarea(attrs={"rows": 2}),
        }


class HeritageCategoryForm(HeritageFormMixin, forms.ModelForm):
    class Meta:
        model = HeritageCategory
        fields = ("code", "name", "description")
        widgets = {
            "code": forms.TextInput(attrs={"placeholder": "e.g., COLONIAL_CHURCH"}),
            "name": forms.TextInput(attrs={"placeholder": "e.g., Spanish Colonial Church"}),
            "description": forms.Textarea(attrs={"rows": 2}),
        }

    def clean_code(self):
        return (self.cleaned_data.get("code") or "").strip().upper().replace(" ", "_")


class VisitationLogForm(HeritageFormMixin, forms.ModelForm):
    """Form enforcing BR-01 demographic origin sum, BR-04 daily uniqueness, and Curator site ownership."""

    class Meta:
        model = VisitationLog
        fields = (
            "site",
            "visit_date",
            "local_visitors",
            "domestic_visitors",
            "foreign_visitors",
            "total_visitors",
            "weather_condition",
            "special_event",
            "remarks",
        )
        widgets = {
            "visit_date": forms.DateInput(attrs={"type": "date"}),
            "local_visitors": forms.NumberInput(attrs={"min": 0, "data-origin-part": "1"}),
            "domestic_visitors": forms.NumberInput(attrs={"min": 0, "data-origin-part": "1"}),
            "foreign_visitors": forms.NumberInput(attrs={"min": 0, "data-origin-part": "1"}),
            "total_visitors": forms.NumberInput(attrs={"min": 1}),
            "special_event": forms.TextInput(
                attrs={"placeholder": "e.g., Sinulog Heritage Walk / School Field Study"}
            ),
            "remarks": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Optional observations on visitor flow or site upkeep..."}
            ),
        }

    def __init__(self, *args, user=None, locked_site=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

        if user is not None:
            if user.is_admin_role:
                self.fields["site"].queryset = HeritageSite.objects.all()
            else:
                self.fields["site"].queryset = HeritageSite.objects.filter(created_by=user)

        if not self.is_bound and not self.instance.pk:
            self.initial.setdefault("visit_date", timezone.localdate().isoformat())
            if locked_site is not None:
                self.initial.setdefault("site", locked_site.pk)

    def clean_visit_date(self):
        visit_date = self.cleaned_data.get("visit_date")
        if visit_date and visit_date > timezone.localdate():
            raise forms.ValidationError("Visitation date cannot be in the future.")
        return visit_date

    def clean(self):
        cleaned = super().clean()
        site = cleaned.get("site")
        visit_date = cleaned.get("visit_date")
        local_v = cleaned.get("local_visitors")
        dom_v = cleaned.get("domestic_visitors")
        for_v = cleaned.get("foreign_visitors")
        total_v = cleaned.get("total_visitors")

        if site and self.user and not self.user.is_admin_role and site.created_by_id != self.user.id:
            self.add_error("site", "You can only record visitation logs for heritage sites you manage.")

        if site and visit_date:
            min_year = max(1900, site.established_year)
            if visit_date.year < min_year:
                self.add_error(
                    "visit_date",
                    f'Visitation date cannot be earlier than {min_year} for "{site.name}".',
                )
            dup_qs = VisitationLog.objects.filter(site=site, visit_date=visit_date)
            if self.instance.pk:
                dup_qs = dup_qs.exclude(pk=self.instance.pk)
            if dup_qs.exists():
                self.add_error(
                    "visit_date",
                    f'A visitation log for "{site.name}" on {visit_date:%b %d, %Y} already exists (BR-04). '
                    "Edit the existing log instead.",
                )

        if None not in (local_v, dom_v, for_v, total_v):
            if total_v <= 0:
                self.add_error("total_visitors", "Total visitors must be at least 1.")
            else:
                origin_sum = local_v + dom_v + for_v
                if origin_sum != total_v:
                    self.add_error(
                        "total_visitors",
                        f"Demographic sum mismatch (BR-01): Local ({local_v}) + Domestic ({dom_v}) "
                        f"+ Foreign ({for_v}) = {origin_sum}, which must equal Total Visitors ({total_v}).",
                    )
        return cleaned
