from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def assign_owner(apps, schema_editor):
    """Існуючим курсам призначаємо власника: першого суперкористувача,
    інакше першого користувача, інакше створюємо demo_owner."""
    Course = apps.get_model("courses", "Course")
    app_label, model_name = settings.AUTH_USER_MODEL.split(".")
    User = apps.get_model(app_label, model_name)
    if not Course.objects.filter(owner__isnull=True).exists():
        return
    owner = (
        User.objects.filter(is_superuser=True).order_by("pk").first()
        or User.objects.order_by("pk").first()
    )
    if owner is None:
        owner = User.objects.create(username="demo_owner", password="!")
    Course.objects.filter(owner__isnull=True).update(owner=owner)


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0004_lesson_constraints"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="course",
            name="owner",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="owned_courses",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(assign_owner, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="course",
            name="owner",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="owned_courses",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
