"""Private, account-owned records for the GLORY faith journey."""
from django.conf import settings
from django.db import models


class FaithReflection(models.Model):
    """A private reflection saved by one authenticated user."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="faith_reflections",
    )
    title = models.CharField(max_length=120, blank=True)
    body = models.TextField(max_length=4000)
    scripture_reference = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title or f"Faith reflection — {self.created_at:%Y-%m-%d}"


class PrayerJournalEntry(models.Model):
    """A private prayer, gratitude note, or answered-prayer record."""

    class EntryType(models.TextChoices):
        PRAYER = "prayer", "Prayer"
        GRATITUDE = "gratitude", "Gratitude"
        ANSWERED = "answered", "Answered prayer"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="prayer_entries",
    )
    entry_type = models.CharField(
        max_length=12, choices=EntryType.choices, default=EntryType.PRAYER
    )
    title = models.CharField(max_length=120, blank=True)
    body = models.TextField(max_length=4000)
    is_answered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title or f"{self.get_entry_type_display()} — {self.created_at:%Y-%m-%d}"
