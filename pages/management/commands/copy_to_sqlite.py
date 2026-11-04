import tempfile
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Копіює всі записи з PostgreSQL у резервну SQLite-базу (db.sqlite3)."

    def handle(self, *args, **options):
        if settings.DATABASES["default"]["ENGINE"] != "django.db.backends.postgresql":
            raise CommandError("Основна БД зараз не PostgreSQL — копіювати нічого.")
        if "sqlite" not in settings.DATABASES:
            raise CommandError("У settings немає псевдоніма 'sqlite'.")

        # 1. Структура таблиць у SQLite
        call_command("migrate", database="sqlite", interactive=False, verbosity=0)

        # 2. Очищаємо SQLite, щоб не було дублікатів і конфліктів id
        call_command("flush", database="sqlite", interactive=False, verbosity=0)
        Permission.objects.using("sqlite").all().delete()
        ContentType.objects.using("sqlite").all().delete()

        # 3. Вивантажуємо всі дані з Postgres і завантажуємо в SQLite
        with tempfile.TemporaryDirectory() as tmp:
            dump = Path(tmp) / "data.json"
            call_command("dumpdata", database="default", output=str(dump), verbosity=0)
            call_command("loaddata", str(dump), database="sqlite", verbosity=1)

        self.stdout.write(self.style.SUCCESS(
            f"Готово: дані скопійовано в {settings.DATABASES['sqlite']['NAME']}"
        ))
