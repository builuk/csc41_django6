from django.conf import settings
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
        call_command("loaddata", "courses", database=alias, verbosity=1)

        self.stdout.write(self.style.SUCCESS(
            f"SQLite готова: {settings.DATABASES[alias]['NAME']}\n"
            "Щоб зайти в адмінку, створіть користувача: python manage.py createsuperuser"
        ))
