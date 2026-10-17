from django.contrib import admin

from .models import FaithReflection, PrayerJournalEntry


@admin.register(FaithReflection)
class FaithReflectionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "title", "scripture_reference", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "title", "body", "scripture_reference")
    readonly_fields = ("created_at", "updated_at")


@admin.register(PrayerJournalEntry)
class PrayerJournalEntryAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "entry_type", "title", "is_answered", "created_at")
    list_filter = ("entry_type", "is_answered", "created_at")
    search_fields = ("user__username", "title", "body")
    readonly_fields = ("created_at",)
