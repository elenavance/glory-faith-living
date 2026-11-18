"""Private, account-owned records for the GLORY faith journey."""
from django.conf import settings
from django.core.validators import MaxLengthValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

class FaithReflection(models.Model):
    """A private reflection saved by one authenticated user."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="faith_reflections",
    )
    title = models.CharField(max_length=120, blank=True)
    body = models.TextField(max_length=4000, validators=[MaxLengthValidator(4000)])
    scripture_reference = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Faith reflection")
        verbose_name_plural = _("Faith reflections")
        indexes = [models.Index(fields=["user", "-created_at"])]

    def __str__(self):
        return self.title or f"Faith reflection — {self.created_at:%Y-%m-%d}"

class PrayerJournalEntry(models.Model):
    """A private prayer, gratitude note, or answered-prayer record."""

    class EntryType(models.TextChoices):
        PRAYER = "prayer", _("Prayer")
        GRATITUDE = "gratitude", _("Gratitude")
        ANSWERED = "answered", _("Answered prayer")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="prayer_entries",
    )
    entry_type = models.CharField(
        max_length=12, choices=EntryType.choices, default=EntryType.PRAYER
    )
    title = models.CharField(max_length=120, blank=True)
    body = models.TextField(max_length=4000, validators=[MaxLengthValidator(4000)])
    scripture_reference = models.CharField(max_length=120, blank=True)
    is_answered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Prayer journal entry")
        verbose_name_plural = _("Prayer journal entries")
        indexes = [models.Index(fields=["user", "-created_at"])]

    def clean(self):
        # Keep is_answered in sync with entry_type
        if self.entry_type == self.EntryType.ANSWERED:
            self.is_answered = True

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title or f"{self.get_entry_type_display()} — {self.created_at:%Y-%m-%d}"
