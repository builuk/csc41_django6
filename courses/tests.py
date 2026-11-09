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

    def test_cbv_matches_fbv(self):
        fbv = self.client.get(
            reverse("courses:detail", args=[self.published.pk])
        )
        cbv = self.client.get(
            reverse("courses:detail-cbv", args=[self.published.pk])
        )
        self.assertEqual(fbv.status_code, 200)
        self.assertEqual(cbv.status_code, 200)
        self.assertEqual(fbv.content, cbv.content)

    def test_cbv_post_not_allowed(self):
        response = self.client.post(
            reverse("courses:detail-cbv", args=[self.published.pk])
        )
        self.assertEqual(response.status_code, 405)

    def test_cbv_draft_hidden_from_guest(self):
        response = self.client.get(
            reverse("courses:detail-cbv", args=[self.draft.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_cbv_missing_course(self):
        response = self.client.get(
            reverse("courses:detail-cbv", args=[999999])
        )
        self.assertEqual(response.status_code, 404)

    def test_templates_show_shared_navigation(self):
        response = self.client.get(reverse("courses:detail", args=[self.published.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Python Backend")
        self.assertContains(response, "Курси")

    def test_course_title_is_escaped(self):
        self.published.title = "<script>alert(1)</script>"
        self.published.save(update_fields=["title"])
        response = self.client.get(reverse("courses:detail", args=[self.published.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "<script>")
        self.assertContains(response, "&lt;script&gt;")

    def test_lessons_empty(self):
        response = self.client.get(reverse("courses:lessons", args=[self.published.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Уроків поки немає.")

    def test_lessons_rendered_in_order(self):
        Lesson.objects.create(course=self.published, title="Другий урок", position=2)
        Lesson.objects.create(course=self.published, title="Перший урок", position=1)
        response = self.client.get(reverse("courses:lessons", args=[self.published.pk]))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertLess(content.index("Перший урок"), content.index("Другий урок"))

    def test_draft_lessons_hidden_from_guest(self):
        response = self.client.get(reverse("courses:lessons", args=[self.draft.pk]))
        self.assertEqual(response.status_code, 404)