from django.db import models
from django.core.validators import MinValueValidator


class Course(models.Model):
    title = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)
    capacity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    status = models.CharField(max_length=12, choices=[
        ("draft", "Чернетка"), ("published", "Опубліковано")
    ], default="draft")
    document = models.FileField(upload_to="course_documents/%Y/%m/", blank=True)

    def __str__(self):
        return self.title

class Lesson(models.Model):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="lessons"
    )
    title = models.CharField(max_length=120)
    position = models.PositiveIntegerField()