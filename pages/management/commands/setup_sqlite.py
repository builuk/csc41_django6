from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Готує SQLite-базу: створює таблиці (migrate) і завантажує "
        "початкові дані з courses/fixtures/courses.json."
    )

    def handle(self, *args, **options):
        # Якщо основна БД — Postgres, працюємо з окремим псевдонімом 'sqlite'
        alias = "sqlite" if "sqlite" in settings.DATABASES else "default"

        call_command("migrate", database=alias, interactive=False, verbosity=1)
        # Курси у fixture посилаються на власника demo_owner (Course.owner)
        User = get_user_model()
        if not User.objects.using(alias).filter(username="demo_owner").exists():
            owner = User(username="demo_owner")
            owner.set_unusable_password()
            owner.save(using=alias)
        call_command("loaddata", "courses", database=alias, verbosity=1)

        self.stdout.write(self.style.SUCCESS(
            f"SQLite готова: {settings.DATABASES[alias]['NAME']}\n"
            "Щоб зайти в адмінку, створіть користувача: python manage.py createsuperuser"
        ))
