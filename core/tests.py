from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import FaithReflection, PrayerJournalEntry, VipTrial

User = get_user_model()


class BasicAppTests(TestCase):
    def test_homepage_loads_and_includes_core_content(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "GLORY")
        self.assertContains(response, "Daily Word")

    def test_language_selector_is_disabled_until_translations_exist(self):
        response = self.client.get("/")
        self.assertContains(response, "Language selection coming soon")
        self.assertContains(response, "disabled")

    def test_favicon_redirects_to_brand_mark(self):
        response = self.client.get("/favicon.ico")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/static/images/glory-mark.svg")

    def test_reminder_ui_discloses_scheduling_is_not_active(self):
        response = self.client.get("/")
        self.assertContains(response, "Reminder scheduling is not available yet")
        self.assertContains(response, "Planned reminder time (not active yet)")

    def test_health_endpoint(self):
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_manifest(self):
        response = self.client.get("/manifest.webmanifest")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["short_name"], "GLORY")

    def test_signup_creates_account_and_signs_user_in(self):
        response = self.client.post(reverse("signup"), {
            "username": "newmember",
            "password1": "A-long-unique-passphrase-482!",
            "password2": "A-long-unique-passphrase-482!",
        })
        self.assertRedirects(response, reverse("journey"))
        self.assertTrue(User.objects.filter(username="newmember").exists())
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_journey_requires_authentication(self):
        response = self.client.get(reverse("journey"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('journey')}")

    def test_user_can_save_private_reflection(self):
        user = User.objects.create_user(username="member-one", password="safe-test-password-123")
        self.client.force_login(user)
        response = self.client.post(reverse("save-reflection"), {
            "title": "Hope in a hard season",
            "scripture_reference": "Psalm 23:1",
            "body": "I can take one step at a time.",
        })
        self.assertRedirects(response, reverse("journey"))
        entry = FaithReflection.objects.get(user=user)
        self.assertEqual(entry.scripture_reference, "Psalm 23:1")
        self.assertEqual(entry.body, "I can take one step at a time.")

    def test_user_cannot_see_another_users_reflection(self):
        owner = User.objects.create_user(username="owner", password="safe-test-password-123")
        other = User.objects.create_user(username="other", password="safe-test-password-123")
        FaithReflection.objects.create(user=owner, title="Private thought", body="Only for me.")
        self.client.force_login(other)
        response = self.client.get(reverse("journey"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Private thought")
        self.assertNotContains(response, "Only for me.")

    def test_user_can_save_prayer_entry(self):
        user = User.objects.create_user(username="prayer-member", password="safe-test-password-123")
        self.client.force_login(user)
        response = self.client.post(reverse("save-prayer"), {
            "entry_type": "gratitude",
            "title": "A small blessing",
            "body": "I am grateful for the people who showed up today.",
        })
        self.assertRedirects(response, reverse("journey"))
        entry = PrayerJournalEntry.objects.get(user=user)
        self.assertEqual(entry.entry_type, PrayerJournalEntry.EntryType.GRATITUDE)

    def test_empty_reflection_is_not_saved(self):
        user = User.objects.create_user(username="member-empty", password="safe-test-password-123")
        self.client.force_login(user)
        self.client.post(reverse("save-reflection"), {"title": "Empty", "body": "   "})
        self.assertFalse(FaithReflection.objects.filter(user=user).exists())

    def test_user_cannot_delete_another_users_reflection(self):
        owner = User.objects.create_user(username="journal-owner", password="safe-test-password-123")
        other = User.objects.create_user(username="journal-other", password="safe-test-password-123")
        entry = FaithReflection.objects.create(user=owner, title="Do not delete", body="Private entry.")
        self.client.force_login(other)
        response = self.client.post(reverse("delete-journal-entry", kwargs={
            "kind": "reflection", "entry_id": entry.pk,
        }))
        self.assertRedirects(response, reverse("journey"))
        self.assertTrue(FaithReflection.objects.filter(pk=entry.pk, user=owner).exists())

    def test_user_can_delete_their_own_prayer_entry(self):
        user = User.objects.create_user(username="journal-delete", password="safe-test-password-123")
        entry = PrayerJournalEntry.objects.create(user=user, title="A prayer", body="Please guide me.")
        self.client.force_login(user)
        response = self.client.post(reverse("delete-journal-entry", kwargs={
            "kind": "prayer", "entry_id": entry.pk,
        }))
        self.assertRedirects(response, reverse("journey"))
        self.assertFalse(PrayerJournalEntry.objects.filter(pk=entry.pk).exists())

    def test_guidance_returns_relevant_scripture_without_storing_question(self):
        question = "I feel anxious and worried about the future."
        response = self.client.post(reverse("guidance"), {"question": question})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["reference"], "Philippians 4:6–7")
        self.assertFalse(response.json()["stored"])

    def test_guidance_rejects_empty_question(self):
        response = self.client.post(reverse("guidance"), {"question": "   "})
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_guidance_rejects_questions_over_limit(self):
        response = self.client.post(reverse("guidance"), {"question": "a" * 701})
        self.assertEqual(response.status_code, 400)



class GuestGuidanceSaveTests(TestCase):
    def test_guest_can_stage_only_the_selected_reflection_for_signup(self):
        response = self.client.post(
            reverse("prepare-reflection-save"),
            {
                "scripture_reference": "Psalm 23:1",
                "passage": "The Lord is my shepherd.",
                "reflection": "I can take the next step without carrying the whole road.",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["saved"])
        self.assertEqual(response.json()["signup_url"], reverse("signup"))
        pending = self.client.session["pending_guidance_reflection"]
        self.assertEqual(pending["scripture_reference"], "Psalm 23:1")
        self.assertNotIn("question", pending)
        self.assertNotIn("question", self.client.session)

    def test_signup_saves_the_selected_guidance_result_privately(self):
        session = self.client.session
        session["pending_guidance_reflection"] = {
            "title": "Scripture reflection: Psalm 23:1",
            "body": "The Lord is my shepherd.\n\nI can take the next step.",
            "scripture_reference": "Psalm 23:1",
        }
        session.save()
        response = self.client.post(
            reverse("signup"),
            {
                "username": "glory-reflection-member",
                "password1": "A-long-unique-passphrase-482!",
                "password2": "A-long-unique-passphrase-482!",
            },
        )
        self.assertRedirects(response, reverse("journey"))
        entry = FaithReflection.objects.get(user__username="glory-reflection-member")
        self.assertEqual(entry.scripture_reference, "Psalm 23:1")
        self.assertIn("I can take the next step.", entry.body)
        self.assertNotIn("pending_guidance_reflection", self.client.session)

    def test_authenticated_user_can_save_guidance_result_without_signup(self):
        user = User.objects.create_user(
            username="glory-signed-in",
            password="safe-test-password-123",
        )
        self.client.force_login(user)
        response = self.client.post(
            reverse("prepare-reflection-save"),
            {
                "scripture_reference": "Psalm 23:1",
                "passage": "The Lord is my shepherd.",
                "reflection": "I can pause and choose a steady next step.",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["saved"])
        self.assertTrue(FaithReflection.objects.filter(user=user).exists())

    def test_guidance_save_rejects_empty_or_oversized_results(self):
        response = self.client.post(
            reverse("prepare-reflection-save"),
            {
                "scripture_reference": "Psalm 23:1",
                "passage": "The Lord is my shepherd.",
                "reflection": "x" * 4000,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(FaithReflection.objects.exists())


class VipTrialTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="vip-member", password="safe-test-password-123")

    def test_viewing_membership_does_not_start_trial(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("membership")).status_code, 200)
        self.assertFalse(VipTrial.objects.filter(user=self.user).exists())

    def test_trial_starts_only_after_explicit_post(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("start-vip-trial"))
        trial = VipTrial.objects.get(user=self.user)
        self.assertRedirects(response, reverse("guided-study"))
        self.assertTrue(trial.is_active)
        expected_month = trial.started_at.month % 12 + 1
        self.assertEqual(trial.ends_at.month, expected_month)
        self.assertContains(self.client.get(reverse("guided-study")), "A week in the")

    def test_restarting_trial_does_not_extend_expiry(self):
        self.client.force_login(self.user)
        self.client.post(reverse("start-vip-trial"))
        original_end = VipTrial.objects.get(user=self.user).ends_at
        self.client.post(reverse("start-vip-trial"))
        self.assertEqual(VipTrial.objects.get(user=self.user).ends_at, original_end)

    def test_guest_cannot_start_trial(self):
        response = self.client.post(reverse("start-vip-trial"))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(VipTrial.objects.exists())

    def test_expired_trial_cannot_open_study_but_journal_remains_free(self):
        from datetime import timedelta
        from django.utils import timezone
        VipTrial.objects.create(
            user=self.user,
            started_at=timezone.now() - timedelta(days=40),
            ends_at=timezone.now() - timedelta(days=10),
        )
        self.client.force_login(self.user)
        self.assertRedirects(self.client.get(reverse("guided-study")), reverse("membership"))
        self.assertEqual(self.client.get(reverse("journey")).status_code, 200)
