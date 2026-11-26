from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import LoginView
from django.core.cache import cache
from django.db.models import Count, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from heritage.analytics import build_visitation_analytics
from heritage.models import District, HeritageSite, VisitationLog

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
    MAX_FAILED_ATTEMPTS = 10
    LOCKOUT_SECONDS = 300

    def _throttle_key(self, request):
        ip = (request.META.get("REMOTE_ADDR") or "unknown").strip()
        username = (request.POST.get("username") or "").strip().lower()
        return f"wi_login_fail:{ip}:{username}"

    def post(self, request, *args, **kwargs):
        key = self._throttle_key(request)
        if cache.get(key, 0) >= self.MAX_FAILED_ATTEMPTS:
            messages.error(
                request,
                "Too many failed login attempts. Please wait 5 minutes before trying again.",
            )
            form = self.get_form()
            return self.render_to_response(self.get_context_data(form=form), status=429)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        cache.delete(self._throttle_key(self.request))
        messages.success(
            self.request,
            f"Welcome back, {form.get_user().get_short_name() or form.get_user().username}!",
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        key = self._throttle_key(self.request)
        attempts = cache.get(key, 0) + 1
        cache.set(key, attempts, self.LOCKOUT_SECONDS)
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
    all_logs = VisitationLog.objects.all()
    analytics = build_visitation_analytics(all_logs)
    top_sites = (
        HeritageSite.objects.select_related("district", "category", "created_by")
        .annotate(
            total_visitors_sum=Coalesce(Sum("visitation_logs__total_visitors"), 0),
            logs_recorded=Count("visitation_logs", distinct=True),
        )
        .order_by("-total_visitors_sum", "name")[:5]
    )
    context = {
        "total_users": User.objects.count(),
        "admin_count": User.objects.filter(role=User.Role.ADMIN).count(),
        "curator_count": User.objects.filter(role=User.Role.CURATOR).count(),
        "viewer_count": User.objects.filter(role=User.Role.VIEWER).count(),
        "recent_users": User.objects.order_by("-date_joined")[:6],
        "total_sites": HeritageSite.objects.count(),
        "analytics": analytics,
        "top_sites": top_sites,
    }
    return render(request, "accounts/dashboards/admin.html", context)


@role_required(User.Role.CURATOR)
def curator_dashboard(request):
    today = timezone.localdate()
    my_sites = (
        HeritageSite.objects.filter(created_by=request.user)
        .select_related("district", "category")
        .annotate(
            total_visitors_sum=Coalesce(Sum("visitation_logs__total_visitors"), 0),
            logs_recorded=Count("visitation_logs", distinct=True),
        )
        .order_by("-total_visitors_sum", "name")
    )
    my_logs = VisitationLog.objects.filter(site__created_by=request.user).select_related("site")
    analytics = build_visitation_analytics(my_logs)
    logs_this_month = my_logs.filter(
        visit_date__year=today.year,
        visit_date__month=today.month,
    ).count()

    context = {
        "my_sites": my_sites[:6],
        "my_site_count": my_sites.count(),
        "analytics": analytics,
        "logs_this_month": logs_this_month,
        "recent_logs": my_logs[:6],
    }
    return render(request, "accounts/dashboards/curator.html", context)


@role_required(User.Role.VIEWER)
def viewer_dashboard(request):
    published_sites = (
        HeritageSite.objects.filter(is_published=True)
        .select_related("district", "category")
        .annotate(
            total_visitors_sum=Coalesce(Sum("visitation_logs__total_visitors"), 0),
            logs_recorded=Count("visitation_logs", distinct=True),
        )
        .order_by("-total_visitors_sum", "name")
    )
    public_logs = VisitationLog.objects.filter(site__is_published=True)
    analytics = build_visitation_analytics(public_logs)

    context = {
        "published_site_count": published_sites.count(),
        "district_count": District.objects.count(),
        "analytics": analytics,
        "top_sites": published_sites[:6],
    }
    return render(request, "accounts/dashboards/viewer.html", context)


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
