from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class StyledFormMixin:
    """Adds a CSS class to every widget so templates stay simple."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = "form-check-input" if isinstance(field.widget, forms.CheckboxInput) else "form-control"
            field.widget.attrs.setdefault("class", css)


class RegistrationForm(StyledFormMixin, UserCreationForm):
    SELF_REGISTER_ROLES = [
        (User.Role.VIEWER, "Viewer – browse heritage dashboards (read-only)"),
        (User.Role.CURATOR, "Curator – manage heritage sites and visitor logs"),
    ]

    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=SELF_REGISTER_ROLES, initial=User.Role.VIEWER)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email", "role")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_role(self):
        role = self.cleaned_data["role"]
        # Administrator accounts can never be self-registered.
        if role not in (User.Role.VIEWER, User.Role.CURATOR):
            raise forms.ValidationError("Invalid role selected.")
        return role

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.role = self.cleaned_data["role"]
        if commit:
            user.save()
        return user


class LoginForm(StyledFormMixin, AuthenticationForm):
    error_messages = {
        "invalid_login": "Invalid username or password. Please try again.",
        "inactive": "This account is inactive.",
    }


class ProfileForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "contact_number", "organization", "bio", "profile_photo")
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 3}),
            "profile_photo": forms.ClearableFileInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
        self.fields["email"].required = True

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email
