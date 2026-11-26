from decimal import Decimal

from django import forms
from django.utils import timezone

from .models import District, HeritageCategory, HeritageSite, PreservationTag


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
