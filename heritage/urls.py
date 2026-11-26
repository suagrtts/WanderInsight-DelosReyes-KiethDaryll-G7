from django.urls import path

from . import views

app_name = "heritage"

urlpatterns = [
    path("sites/", views.site_list, name="site_list"),
    path("sites/new/", views.site_create, name="site_create"),
    path("sites/<slug:slug>/", views.site_detail, name="site_detail"),
    path("sites/<slug:slug>/edit/", views.site_update, name="site_update"),
    path("sites/<slug:slug>/delete/", views.site_delete, name="site_delete"),
    path("sites/<slug:slug>/logs/new/", views.log_create, name="site_log_create"),
    path("logs/", views.log_list, name="log_list"),
    path("logs/new/", views.log_create, name="log_create"),
    path("logs/<int:pk>/edit/", views.log_update, name="log_update"),
    path("logs/<int:pk>/delete/", views.log_delete, name="log_delete"),
    path("taxonomy/", views.taxonomy_manage, name="taxonomy_manage"),
]
