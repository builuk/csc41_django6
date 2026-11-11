from django.db import models
from django.core.validators import MinValueValidator


class Course(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Чернетка"
        PUBLISHED = "published", "Опубліковано"

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
        indexes = [
            models.Index(fields=["status", "title"], name="course_status_title")
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(capacity__gte=1),
                name="course_capacity_gte_1",
            ),
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
