from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date

from accounts.decorators import role_required
from accounts.models import User

from .analytics import build_visitation_analytics
from .forms import DistrictForm, HeritageCategoryForm, HeritageSiteForm, VisitationLogForm
from .models import District, HeritageCategory, HeritageSite, VisitationLog


@login_required
def site_list(request):
    """Role-aware Heritage Site Registry with search, taxonomy filters, and visitor totals (SDD F-02)."""
    user = request.user
    if user.is_admin_role:
        scope = request.GET.get("scope", "all")
        if scope == "mine":
            sites_qs = HeritageSite.objects.filter(created_by=user)
        else:
            scope = "all"
            sites_qs = HeritageSite.objects.all()
    elif user.is_curator:
        scope = request.GET.get("scope", "mine")
        if scope == "catalog":
            sites_qs = HeritageSite.objects.filter(Q(is_published=True) | Q(created_by=user))
        else:
            scope = "mine"
            sites_qs = HeritageSite.objects.filter(created_by=user)
    else:
        scope = "catalog"
        sites_qs = HeritageSite.objects.filter(is_published=True)

    sites_qs = (
        sites_qs.select_related("district", "category", "created_by")
        .prefetch_related("preservation_tags")
        .annotate(
            all_time_visitors=Coalesce(Sum("visitation_logs__total_visitors"), 0),
            log_count=Count("visitation_logs", distinct=True),
        )
    )

    q = (request.GET.get("q") or "").strip()
    district_id = (request.GET.get("district") or "").strip()
    category_id = (request.GET.get("category") or "").strip()
    status = (request.GET.get("status") or "").strip()

    if q:
        sites_qs = sites_qs.filter(
            Q(name__icontains=q)
            | Q(municipality__icontains=q)
            | Q(custodian_organization__icontains=q)
            | Q(historical_overview__icontains=q)
        )
    if district_id.isdigit():
        sites_qs = sites_qs.filter(district_id=int(district_id))
    if category_id.isdigit():
        sites_qs = sites_qs.filter(category_id=int(category_id))
    if status in dict(HeritageSite.PreservationStatus.choices):
        sites_qs = sites_qs.filter(preservation_status=status)

    paginator = Paginator(sites_qs.order_by("name", "id"), 20)
    page_obj = paginator.get_page(request.GET.get("page"))
    sites = list(page_obj.object_list)
    for site in sites:
        site.user_can_manage = site.can_manage(user)

    query_params = request.GET.copy()
    query_params.pop("page", None)

    context = {
        "sites": sites,
        "page_obj": page_obj,
        "querystring": query_params.urlencode(),
        "scope": scope,
        "q": q,
        "selected_district": district_id,
        "selected_category": category_id,
        "selected_status": status,
        "districts": District.objects.all(),
        "categories": HeritageCategory.objects.all(),
        "status_choices": HeritageSite.PreservationStatus.choices,
        "my_site_count": HeritageSite.objects.filter(created_by=user).count()
        if (user.is_curator or user.is_admin_role)
        else 0,
        "published_site_count": HeritageSite.objects.filter(is_published=True).count(),
        "total_site_count": HeritageSite.objects.count(),
    }
    return render(request, "heritage/site_list.html", context)


@login_required
def site_detail(request, slug):
    """Detailed profile view for a Heritage Site with live visitation analytics and logs."""
    site = get_object_or_404(
        HeritageSite.objects.select_related("district", "category", "created_by").prefetch_related(
            "preservation_tags"
        ),
        slug=slug,
    )
    can_manage = site.can_manage(request.user)
    if not site.is_published and not can_manage:
        messages.error(request, "You do not have permission to view this unpublished heritage site.")
        return redirect("heritage:site_list")

    logs_qs = site.visitation_logs.select_related("recorded_by").all()
    analytics = build_visitation_analytics(logs_qs)
    logs_page = Paginator(logs_qs, 15).get_page(request.GET.get("page"))
    recent_logs = list(logs_page.object_list)
    for log in recent_logs:
        log.user_can_manage = log.can_manage(request.user)

    context = {
        "site": site,
        "can_manage": can_manage,
        "analytics": analytics,
        "recent_logs": recent_logs,
        "page_obj": logs_page,
    }
    return render(request, "heritage/site_detail.html", context)


@role_required(User.Role.CURATOR, User.Role.ADMIN)
def site_create(request):
    """Register a new Heritage Site linked to the authenticated Curator/Admin."""
    if request.method == "POST":
        form = HeritageSiteForm(request.POST)
        if form.is_valid():
            site = form.save(commit=False)
            site.created_by = request.user
            site.save()
            form.save_m2m()
            messages.success(
                request,
                f'Heritage site "{site.name}" has been registered in {site.district.name}.',
            )
            return redirect("heritage:site_detail", slug=site.slug)
        messages.error(request, "Please correct the highlighted validation errors below.")
    else:
        form = HeritageSiteForm()

    return render(
        request,
        "heritage/site_form.html",
        {
            "form": form,
            "is_edit": False,
        },
    )


@role_required(User.Role.CURATOR, User.Role.ADMIN)
def site_update(request, slug):
    """Update an existing Heritage Site; Curators can only modify their own records."""
    site = get_object_or_404(HeritageSite, slug=slug)
    if not site.can_manage(request.user):
        messages.error(request, "You can only edit heritage sites that you registered.")
        return redirect("heritage:site_detail", slug=site.slug)

    if request.method == "POST":
        form = HeritageSiteForm(request.POST, instance=site)
        if form.is_valid():
            updated_site = form.save()
            messages.success(request, f'Changes to "{updated_site.name}" have been saved.')
            return redirect("heritage:site_detail", slug=updated_site.slug)
        messages.error(request, "Please correct the highlighted validation errors below.")
    else:
        form = HeritageSiteForm(instance=site)

    return render(
        request,
        "heritage/site_form.html",
        {
            "form": form,
            "site": site,
            "is_edit": True,
        },
    )


@role_required(User.Role.CURATOR, User.Role.ADMIN)
def site_delete(request, slug):
    """Confirm and delete a Heritage Site; Curators can only delete their own records."""
    site = get_object_or_404(
        HeritageSite.objects.select_related("district", "category", "created_by"),
        slug=slug,
    )
    if not site.can_manage(request.user):
        messages.error(request, "You can only delete heritage sites that you registered.")
        return redirect("heritage:site_detail", slug=site.slug)

    if request.method == "POST":
        site_name = site.name
        site.delete()
        messages.success(request, f'Heritage site "{site_name}" has been removed from the registry.')
        return redirect("heritage:site_list")

    return render(request, "heritage/site_confirm_delete.html", {"site": site})


@role_required(User.Role.CURATOR, User.Role.ADMIN)
def log_list(request):
    """List daily visitation logs scoped to Curator's own sites or all sites for Administrators."""
    user = request.user
    if user.is_admin_role:
        logs_qs = VisitationLog.objects.select_related("site", "site__district", "recorded_by").all()
        available_sites = HeritageSite.objects.all()
    else:
        logs_qs = VisitationLog.objects.select_related("site", "site__district", "recorded_by").filter(
            Q(site__created_by=user) | Q(recorded_by=user)
        )
        available_sites = HeritageSite.objects.filter(created_by=user)

    site_id = (request.GET.get("site") or "").strip()
    weather = (request.GET.get("weather") or "").strip()
    date_from = (request.GET.get("date_from") or "").strip()
    date_to = (request.GET.get("date_to") or "").strip()

    if site_id.isdigit():
        logs_qs = logs_qs.filter(site_id=int(site_id))
    if weather in dict(VisitationLog.WeatherCondition.choices):
        logs_qs = logs_qs.filter(weather_condition=weather)

    parsed_from = None
    parsed_to = None
    if date_from:
        parsed_from = parse_date(date_from)
        if parsed_from is None:
            messages.warning(request, "Invalid 'From Date' filter ignored. Use YYYY-MM-DD format.")
            date_from = ""
        else:
            logs_qs = logs_qs.filter(visit_date__gte=parsed_from)
    if date_to:
        parsed_to = parse_date(date_to)
        if parsed_to is None:
            messages.warning(request, "Invalid 'To Date' filter ignored. Use YYYY-MM-DD format.")
            date_to = ""
        else:
            logs_qs = logs_qs.filter(visit_date__lte=parsed_to)
    if parsed_from and parsed_to and parsed_from > parsed_to:
        messages.warning(request, "Start date cannot be later than end date.")

    analytics = build_visitation_analytics(logs_qs)
    page_obj = Paginator(logs_qs, 25).get_page(request.GET.get("page"))
    logs = list(page_obj.object_list)
    for log in logs:
        log.user_can_manage = log.can_manage(user)

    query_params = request.GET.copy()
    query_params.pop("page", None)

    return render(
        request,
        "heritage/log_list.html",
        {
            "logs": logs,
            "page_obj": page_obj,
            "querystring": query_params.urlencode(),
            "analytics": analytics,
            "available_sites": available_sites,
            "weather_choices": VisitationLog.WeatherCondition.choices,
            "selected_site": site_id,
            "selected_weather": weather,
            "date_from": date_from,
            "date_to": date_to,
        },
    )


@role_required(User.Role.CURATOR, User.Role.ADMIN)
def log_create(request, slug=None):
    """Record a new daily VisitationLog enforcing BR-01, BR-04, and Curator site ownership."""
    locked_site = None
    if slug is not None:
        locked_site = get_object_or_404(HeritageSite, slug=slug)
        if not locked_site.can_manage(request.user):
            messages.error(request, "You can only log visitation for heritage sites that you manage.")
            return redirect("heritage:site_detail", slug=locked_site.slug)

    manageable_sites = (
        HeritageSite.objects.all()
        if request.user.is_admin_role
        else HeritageSite.objects.filter(created_by=request.user)
    )
    if not manageable_sites.exists():
        messages.info(
            request,
            "Register a heritage site under your custodianship first before recording daily visitation.",
        )
        return redirect("heritage:site_create")

    if request.method == "POST":
        form = VisitationLogForm(request.POST, user=request.user, locked_site=locked_site)
        if form.is_valid():
            log = form.save(commit=False)
            log.recorded_by = request.user
            log.save()
            if log.total_visitors > log.site.daily_capacity:
                messages.warning(
                    request,
                    f'Recorded {log.total_visitors} visitors, exceeding {log.site.name}\'s '
                    f'recommended daily conservation capacity ({log.site.daily_capacity}).',
                )
            messages.success(
                request,
                f'Visitation log saved for "{log.site.name}" ({log.visit_date:%b %d, %Y} · {log.total_visitors} visitors).',
            )
            return redirect("heritage:site_detail", slug=log.site.slug)
        messages.error(request, "Please resolve the visitation validation errors below.")
    else:
        form = VisitationLogForm(user=request.user, locked_site=locked_site)

    return render(
        request,
        "heritage/log_form.html",
        {
            "form": form,
            "locked_site": locked_site,
            "is_edit": False,
        },
    )


@role_required(User.Role.CURATOR, User.Role.ADMIN)
def log_update(request, pk):
    """Update an existing VisitationLog; restricted to managing Curator or Administrator."""
    log = get_object_or_404(VisitationLog.objects.select_related("site", "recorded_by"), pk=pk)
    if not log.can_manage(request.user):
        messages.error(request, "You do not have permission to edit that visitation log.")
        return redirect("heritage:site_detail", slug=log.site.slug)

    if request.method == "POST":
        form = VisitationLogForm(request.POST, instance=log, user=request.user)
        if form.is_valid():
            updated_log = form.save()
            if updated_log.total_visitors > updated_log.site.daily_capacity:
                messages.warning(
                    request,
                    f'Recorded {updated_log.total_visitors} visitors, exceeding {updated_log.site.name}\'s '
                    f'recommended daily conservation capacity ({updated_log.site.daily_capacity}).',
                )
            messages.success(
                request,
                f'Visitation log for "{updated_log.site.name}" ({updated_log.visit_date:%b %d, %Y}) updated.',
            )
            return redirect("heritage:site_detail", slug=updated_log.site.slug)
        messages.error(request, "Please resolve the visitation validation errors below.")
    else:
        form = VisitationLogForm(instance=log, user=request.user)

    return render(
        request,
        "heritage/log_form.html",
        {
            "form": form,
            "log": log,
            "locked_site": log.site,
            "is_edit": True,
        },
    )


@role_required(User.Role.CURATOR, User.Role.ADMIN)
def log_delete(request, pk):
    """Confirm and delete a VisitationLog; restricted to managing Curator or Administrator."""
    log = get_object_or_404(VisitationLog.objects.select_related("site", "recorded_by"), pk=pk)
    if not log.can_manage(request.user):
        messages.error(request, "You do not have permission to delete that visitation log.")
        return redirect("heritage:site_detail", slug=log.site.slug)

    if request.method == "POST":
        site_slug = log.site.slug
        site_name = log.site.name
        log_date = log.visit_date
        log.delete()
        messages.success(
            request,
            f'Visitation log for "{site_name}" on {log_date:%b %d, %Y} has been deleted.',
        )
        return redirect("heritage:site_detail", slug=site_slug)

    return render(request, "heritage/log_confirm_delete.html", {"log": log})


@role_required(User.Role.ADMIN)
def taxonomy_manage(request):
    """Administrator governance view to inspect and add Districts and Heritage Categories."""
    district_form = DistrictForm(prefix="dist")
    category_form = HeritageCategoryForm(prefix="cat")

    if request.method == "POST":
        form_kind = request.POST.get("form_kind")
        if form_kind == "district":
            district_form = DistrictForm(request.POST, prefix="dist")
            if district_form.is_valid():
                district = district_form.save()
                messages.success(request, f'District "{district.name}" added to taxonomy.')
                return redirect("heritage:taxonomy_manage")
            messages.error(request, "Could not add district. Please fix the errors below.")
        elif form_kind == "category":
            category_form = HeritageCategoryForm(request.POST, prefix="cat")
            if category_form.is_valid():
                cat = category_form.save()
                messages.success(request, f'Heritage category "{cat.name}" added to taxonomy.')
                return redirect("heritage:taxonomy_manage")
            messages.error(request, "Could not add category. Please fix the errors below.")

    districts = District.objects.annotate(site_count=Count("sites")).order_by("name")
    categories = HeritageCategory.objects.annotate(site_count=Count("sites")).order_by("name")
    return render(
        request,
        "heritage/taxonomy_manage.html",
        {
            "districts": districts,
            "categories": categories,
            "district_form": district_form,
            "category_form": category_form,
        },
    )
