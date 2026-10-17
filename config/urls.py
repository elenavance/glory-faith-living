"""URL configuration for GLORY."""
from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from core import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("health/", views.health, name="health"),
    path("manifest.webmanifest", views.manifest, name="manifest"),
    path("service-worker.js", views.service_worker, name="service-worker"),
    path("offline/", TemplateView.as_view(template_name="offline.html"), name="offline"),
]
