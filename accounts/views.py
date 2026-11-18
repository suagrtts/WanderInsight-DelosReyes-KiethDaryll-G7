from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .decorators import role_required
from .forms import LoginForm, ProfileForm, RegistrationForm
from .models import User

DASHBOARD_BY_ROLE = {
    User.Role.ADMIN: "accounts:admin_dashboard",
    User.Role.CURATOR: "accounts:curator_dashboard",
    User.Role.VIEWER: "accounts:viewer_dashboard",
}


def register_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Account created successfully for {user.username}! You can now log in.")
            return redirect("accounts:login")
        messages.error(request, "Please correct the errors below.")
    else:
        form = RegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


class UserLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, f"Welcome back, {form.get_user().get_short_name() or form.get_user().username}!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Login failed. Invalid username or password.")
        return super().form_invalid(form)


@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("accounts:login")


@login_required
def dashboard_redirect(request):
    """Send each user to the dashboard for their role."""
    return redirect(DASHBOARD_BY_ROLE.get(request.user.role, "accounts:viewer_dashboard"))


@role_required(User.Role.ADMIN)
def admin_dashboard(request):
    context = {
        "total_users": User.objects.count(),
        "admin_count": User.objects.filter(role=User.Role.ADMIN).count(),
        "curator_count": User.objects.filter(role=User.Role.CURATOR).count(),
        "viewer_count": User.objects.filter(role=User.Role.VIEWER).count(),
        "recent_users": User.objects.order_by("-date_joined")[:8],
    }
    return render(request, "accounts/dashboards/admin.html", context)


@role_required(User.Role.CURATOR)
def curator_dashboard(request):
    return render(request, "accounts/dashboards/curator.html")


@role_required(User.Role.VIEWER)
def viewer_dashboard(request):
    return render(request, "accounts/dashboards/viewer.html")


@login_required
def profile_view(request):
    # Always the logged-in user's own profile; no user id in the URL.
    return render(request, "accounts/profile.html", {"profile_user": request.user})


@login_required
def profile_edit(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect("accounts:profile")
        messages.error(request, "Please correct the errors below.")
    else:
        form = ProfileForm(instance=request.user)
    return render(request, "accounts/profile_edit.html", {"form": form})


@login_required
def password_change(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password has been changed.")
            return redirect("accounts:profile")
        messages.error(request, "Please correct the errors below.")
    else:
        form = PasswordChangeForm(request.user)
    for field in form.fields.values():
        field.widget.attrs.setdefault("class", "form-control")
    return render(request, "accounts/password_change.html", {"form": form})
