"""URL configuration for GLORY."""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from django.views.generic import TemplateView
from core import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("accounts/signup/", views.sign_up, name="signup"),
    path("accounts/login/", auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("my-journey/", views.journey, name="journey"),
    path("my-journey/reflection/save/", views.save_reflection, name="save-reflection"),
    path("my-journey/prayer/save/", views.save_prayer, name="save-prayer"),
    path("my-journey/<str:kind>/<int:entry_id>/delete/", views.delete_journal_entry, name="delete-journal-entry"),
    path("health/", views.health, name="health"),
    path("manifest.webmanifest", views.manifest, name="manifest"),
    path("service-worker.js", views.service_worker, name="service-worker"),
    path("offline/", TemplateView.as_view(template_name="offline.html"), name="offline"),
]
