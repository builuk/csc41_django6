from django.http import HttpResponse
from .models import Course
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_safe

def course_list(request):
    return HttpResponse("Список курсів EduHub")

def course_create(request):
    return HttpResponse("Форма створення курсу (демо)")

def course_detail(request, pk):
    return HttpResponse(f"Курс #{pk}; тип: {type(pk).__name__}")

def course_by_slug(request, slug):
    return HttpResponse(f"Slug курсу: {slug}")

def course_search(request):
    query = request.GET.get("q", "")
    return HttpResponse(f"Пошук: {query}")

def visible_courses(user):
    if user.is_authenticated and user.is_staff:
        return Course.objects.all()
    return Course.objects.filter(status="published")

@require_safe
def course_detail(request, pk):
    course = get_object_or_404(visible_courses(request.user), pk=pk)
    return render(request, "courses/detail.html", {"course": course})