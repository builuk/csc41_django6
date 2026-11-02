from django.test import TestCase
from django.urls import reverse
from .models import Course

class CourseViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.published = Course.objects.create(
            title="Python Backend", slug="python", capacity=12, status="published")
        cls.draft = Course.objects.create(
            title="Чернетка", slug="draft", capacity=5, status="draft")

    def test_html(self):
        url = reverse("courses:detail", args=[self.published.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("text/html"))
        self.assertContains(response, "Python Backend")

    def test_json_contract(self):
        url = reverse("courses:json", args=[self.published.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("application/json"))
        self.assertEqual(response.json(), {
            "id": self.published.pk,
            "title": "Python Backend",
            "capacity": 12,
        })

    def test_draft_hidden_from_guest(self):
        response = self.client.get(reverse("courses:json", args=[self.draft.pk]))
        self.assertEqual(response.status_code, 404)

    def test_post_not_allowed_on_read_only(self):
        response = self.client.post(reverse("courses:detail", args=[self.published.pk]))
        self.assertEqual(response.status_code, 405)

    def test_missing_course(self):
        response = self.client.get(reverse("courses:detail", args=[999999]))
        self.assertEqual(response.status_code, 404)