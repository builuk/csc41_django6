from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Course(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Чернетка"
        PUBLISHED = "published", "Опубліковано"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_courses",
    )
    title = models.CharField(max_length=150)
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.DRAFT
    )
    slug = models.SlugField(unique=True)
    capacity = models.PositiveIntegerField(
        default=10, validators=[MinValueValidator(1)]
    )
    document = models.FileField(upload_to="course_documents/%Y/%m/", blank=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ["title", "pk"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(capacity__gte=1),
                name="course_capacity_gte_1",
            ),
        ]
        indexes = [
            models.Index(fields=["status", "title"], name="course_status_title"),
        ]


class Lesson(models.Model):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="lessons"
    )
    title = models.CharField(max_length=120)
    position = models.PositiveIntegerField()

    class Meta:
        ordering = ["position", "pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["course", "position"],
                name="lesson_position_per_course",
            ),
        ]

    def __str__(self):
        return self.title


class Assignment(models.Model):
    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, related_name="assignments"
    )
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["pk"]

    def __str__(self):
        return self.title
