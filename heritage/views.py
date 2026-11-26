from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from accounts.models import User

from .forms import DistrictForm, HeritageCategoryForm, HeritageSiteForm
from .models import District, HeritageCategory, HeritageSite


@login_required
def site_list(request):
    """Role-aware Heritage Site Registry with search and taxonomy filters (SDD F-02)."""
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

    sites_qs = sites_qs.select_related("district", "category", "created_by").prefetch_related(
        "preservation_tags"
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

    sites = list(sites_qs)
    for site in sites:
        site.user_can_manage = site.can_manage(user)

    context = {
        "sites": sites,
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
    """Detailed profile view for a Heritage Site with RBAC visibility check."""
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

    context = {
        "site": site,
        "can_manage": can_manage,
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
