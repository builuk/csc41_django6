from pathlib import Path
from django import forms
from .models import Course


MAX_FILE_SIZE = 100 * 1024


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ["title", "document"]

    def clean_document(self):
        uploaded = self.cleaned_data.get("document")
        if not uploaded:
            return uploaded
        # Під час редагування без нового upload Django може повернути
        # наявний FieldFile: не перечитуємо його як новий файл.
        if not hasattr(uploaded, "size"):
            raise forms.ValidationError("Некоректний файл.")
        if Path(uploaded.name).suffix.lower() != ".txt":
            raise forms.ValidationError("Дозволено лише .txt файли.")
        if uploaded.size > MAX_FILE_SIZE:
            raise forms.ValidationError("Файл має бути не більший за 100 КБ.")
        try:
            data = uploaded.read()
            if b"\x00" in data:
                raise forms.ValidationError("Файл містить нульові байти.")
            data.decode("utf-8")
        except UnicodeDecodeError:
            raise forms.ValidationError("Файл має бути в кодуванні UTF-8.")
        finally:
            uploaded.seek(0)
        return uploaded
