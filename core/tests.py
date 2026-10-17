from django.test import TestCase, Client
from django.urls import reverse

class BasicAppTests(TestCase):
    def test_homepage_loads_and_includes_core_content(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "GLORY")
        self.assertContains(response, "Daily Word")

    def test_health_endpoint(self):
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_manifest(self):
        response = self.client.get("/manifest.webmanifest")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["short_name"], "GLORY")
