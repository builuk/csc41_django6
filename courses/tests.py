from pathlib import Path
from tempfile import TemporaryDirectory
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase, override_settings
from django.urls import reverse
from .models import Assignment, Course, Lesson


class CourseViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user(
            username="owner", password="test-only")
        cls.published = Course.objects.create(
            owner=cls.owner, title="Python Backend", slug="python",
            capacity=12, status="published")
        cls.draft = Course.objects.create(
            owner=cls.owner, title="Чернетка", slug="draft",
            capacity=5, status="draft")

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

class CourseUploadTests(TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        override = override_settings(MEDIA_ROOT=self.temp.name)
        override.enable()
        self.addCleanup(override.disable)
        self.url = reverse("courses:create")
        self.staff = get_user_model().objects.create_user(
            username="staff", password="test-only", is_staff=True)
        self.client.force_login(self.staff)

    def uploaded(self, name, data):
        return SimpleUploadedFile(name, data, content_type="text/plain")

    def files_on_disk(self):
        return [p for p in Path(self.temp.name).rglob("*") if p.is_file()]

    def test_valid_utf8_txt_saved(self):
        response = self.client.post(self.url, {
            "title": "Python", "document": self.uploaded("notes.txt", "Привіт".encode("utf-8")),
        })
        self.assertRedirects(response, reverse("courses:list"))
        course = Course.objects.get()
        self.assertEqual(course.owner, self.staff)
        self.assertTrue(course.document.name.startswith("course_documents/"))
        self.assertTrue(course.document.name.endswith("notes.txt"))
        with course.document.open("rb") as f:
            self.assertEqual(f.read(), "Привіт".encode("utf-8"))
        self.assertEqual(len(self.files_on_disk()), 1)

    def test_optional_document(self):
        response = self.client.post(self.url, {"title": "Без файлу"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Course.objects.count(), 1)
        self.assertEqual(len(self.files_on_disk()), 0)

    def assert_rejected(self, name, data):
        response = self.client.post(self.url, {
            "title": "Невалідний", "document": self.uploaded(name, data),
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="errorlist"')
        self.assertEqual(Course.objects.count(), 0)
        self.assertEqual(len(self.files_on_disk()), 0)

    def test_html_rejected(self):
        self.assert_rejected("page.html", b"<h1>hello</h1>")

    def test_invalid_utf8_rejected(self):
        self.assert_rejected("bad.txt", b"\xff\xfe")

    def test_too_large_rejected(self):
        self.assert_rejected("big.txt", b"a" * (100 * 1024 + 1))

    def test_null_byte_rejected(self):
        self.assert_rejected("binary.txt", b"hello\x00world")

    def test_edit_title_without_replacing_document(self):
        self.client.post(self.url, {
            "title": "До", "document": self.uploaded("notes.txt", b"hello"),
        })
        course = Course.objects.get()
        old_name = course.document.name
        response = self.client.post(reverse("courses:edit", args=[course.pk]), {"title": "Після"})
        self.assertEqual(response.status_code, 302)
        course.refresh_from_db()
        self.assertEqual(course.title, "Після")
        self.assertEqual(course.document.name, old_name)
        self.assertEqual(len(self.files_on_disk()), 1)

    def test_guest_cannot_create_course(self):
        self.client.logout()
        response = self.client.post(self.url, {"title": "Гість"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Course.objects.count(), 0)


class ModelDemoTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            username="teacher", password="test-only"
        )
        self.course = Course.objects.create(
            owner=self.owner, title="Python", slug="python-models", capacity=20
        )
        self.lesson = Lesson.objects.create(
            course=self.course, title="Intro", position=1
        )
        self.assignment = Assignment.objects.create(
            lesson=self.lesson, title="Task"
        )

    def test_reverse_relations(self):
        self.assertEqual(self.course.lessons.count(), 1)
        self.assertEqual(self.lesson.assignments.count(), 1)
        self.assertEqual(self.owner.owned_courses.count(), 1)

    def test_duplicate_lesson_position(self):
        duplicate = Lesson(course=self.course, title="Duplicate", position=1)
        with self.assertRaises(ValidationError):
            duplicate.full_clean()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Lesson.objects.create(
                    course=self.course, title="Duplicate", position=1
                )

    def test_same_position_in_other_course_allowed(self):
        other = Course.objects.create(
            owner=self.owner, title="Django", slug="django-models", capacity=10
        )
        Lesson.objects.create(course=other, title="Intro", position=1)
        self.assertEqual(Lesson.objects.filter(position=1).count(), 2)

    def test_capacity_validation_and_constraint(self):
        invalid = Course(
            owner=self.owner, title="Invalid", slug="invalid", capacity=0
        )
        with self.assertRaises(ValidationError):
            invalid.full_clean()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Course.objects.create(
                    owner=self.owner, title="Invalid", slug="invalid", capacity=0
                )

    def test_status_and_ordering(self):
        self.course.status = Course.Status.PUBLISHED
        self.assertEqual(self.course.get_status_display(), "Опубліковано")
        Lesson.objects.create(course=self.course, title="Third", position=3)
        Lesson.objects.create(course=self.course, title="Second", position=2)
        self.assertEqual(
            list(self.course.lessons.values_list("position", flat=True)),
            [1, 2, 3],
        )

    def test_cascade_and_protect(self):
        course_id = self.course.pk
        lesson_id = self.lesson.pk
        assignment_id = self.assignment.pk
        with self.assertRaises(ProtectedError):
            self.owner.delete()
        self.course.delete()
        self.assertFalse(Course.objects.filter(pk=course_id).exists())
        self.assertFalse(Lesson.objects.filter(pk=lesson_id).exists())
        self.assertFalse(Assignment.objects.filter(pk=assignment_id).exists())
        self.assertTrue(
            get_user_model().objects.filter(pk=self.owner.pk).exists()
        )

    def test_slug_generated_when_missing(self):
        c1 = Course.objects.create(owner=self.owner, title="Django", capacity=15)
        c2 = Course.objects.create(owner=self.owner, title="Django", capacity=15)
        c3 = Course.objects.create(owner=self.owner, title="Основи", capacity=5)
        self.assertEqual(c1.slug, "django")
        self.assertEqual(c2.slug, "django-2")
        self.assertEqual(c3.slug, "course")


class ModelRulesTests(TestCase):
    """Тести до контрольних запитань блоку 6 методпакета пари 20."""

    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            username="rules", password="test-only"
        )
        self.course = Course.objects.create(
            owner=self.owner, title="Python", capacity=20
        )

    # 1. save() НЕ викликає full_clean() автоматично
    # 11. choices не створюють SQL CHECK
    def test_save_skips_validation_and_choices_not_in_db(self):
        self.course.status = "archived"  # значення поза Status.choices
        self.course.save()  # жодної помилки: save() не перевіряє choices
        self.course.refresh_from_db()
        self.assertEqual(self.course.status, "archived")
        with self.assertRaises(ValidationError) as ctx:
            self.course.full_clean()
        self.assertIn("status", ctx.exception.message_dict)

    # 3. PositiveIntegerField дозволяє 0
    def test_positive_integer_field_allows_zero_position(self):
        lesson = Lesson(course=self.course, title="Нульовий", position=0)
        lesson.full_clean()  # не падає
        lesson.save()
        self.assertEqual(lesson.position, 0)

    # 4. Index — не правило унікальності
    def test_index_does_not_forbid_duplicates(self):
        Course.objects.create(owner=self.owner, title="Python", capacity=5)
        self.assertEqual(
            Course.objects.filter(status="draft", title="Python").count(), 2
        )

    # 9. QuerySet.update() оминає validators, але не обмеження БД
    def test_update_bypasses_validators_but_not_db_constraint(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Course.objects.filter(pk=self.course.pk).update(capacity=0)
        self.course.refresh_from_db()
        self.assertEqual(self.course.capacity, 20)

    # 10. get_status_display() повертає людський підпис
    def test_default_status_and_display(self):
        self.assertEqual(self.course.status, Course.Status.DRAFT)
        self.assertEqual(self.course.get_status_display(), "Чернетка")

    # 12. ordering = ["title", "pk"] дає стабільний порядок
    def test_course_ordering_by_title_then_pk(self):
        b = Course.objects.create(owner=self.owner, title="Django", capacity=5)
        c = Course.objects.create(owner=self.owner, title="Django", capacity=5)
        self.assertEqual(
            list(Course.objects.values_list("pk", flat=True)),
            [b.pk, c.pk, self.course.pk],
        )

    # Index і constraints справді оголошені в Meta
    def test_meta_declares_index_and_constraints(self):
        self.assertIn(
            "course_status_title", [i.name for i in Course._meta.indexes]
        )
        self.assertIn(
            "course_capacity_gte_1", [c.name for c in Course._meta.constraints]
        )
        self.assertIn(
            "lesson_position_per_course",
            [c.name for c in Lesson._meta.constraints],
        )
        # UniqueConstraint стоїть у Lesson, а не в Course
        self.assertNotIn(
            "lesson_position_per_course",
            [c.name for c in Course._meta.constraints],
        )

    # CASCADE: видалення уроку видаляє його завдання, але не курс
    def test_lesson_delete_cascades_to_assignments_only(self):
        lesson = Lesson.objects.create(course=self.course, title="L", position=1)
        Assignment.objects.create(lesson=lesson, title="A1")
        Assignment.objects.create(lesson=lesson, title="A2")
        lesson.delete()
        self.assertEqual(Assignment.objects.count(), 0)
        self.assertTrue(Course.objects.filter(pk=self.course.pk).exists())

    # Після delete() pk стає None — повторне видалення неможливе
    def test_second_delete_raises_value_error(self):
        self.course.delete()
        self.assertIsNone(self.course.pk)
        with self.assertRaises(ValueError):
            self.course.delete()

    # Явно переданий slug не перезаписується
    def test_explicit_slug_is_kept(self):
        course = Course.objects.create(
            owner=self.owner, title="Python", slug="my-python", capacity=5
        )
        self.assertEqual(course.slug, "my-python")

    def test_str_returns_title(self):
        lesson = Lesson.objects.create(course=self.course, title="Вступ", position=1)
        assignment = Assignment.objects.create(lesson=lesson, title="Практика")
        self.assertEqual(str(self.course), "Python")
        self.assertEqual(str(lesson), "Вступ")
        self.assertEqual(str(assignment), "Практика")
