from django.http import HttpResponse
from .models import Course
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_safe
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required


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

@require_safe
def course_json(request, pk):
    course = get_object_or_404(visible_courses(request.user), pk=pk)
    return JsonResponse({
        "id": course.pk,
        "title": course.title,
        "capacity": course.capacity,
    })

@require_safe
def course_list(request):
    courses = visible_courses(request.user).order_by("pk")
    return render(request, "courses/list.html", {"courses": courses})

@staff_member_required
@require_http_methods(["POST"])
def course_create(request):
    title = request.POST.get("title", "").strip()
    slug = request.POST.get("slug", "").strip()
    capacity_raw = request.POST.get("capacity", "")
    if not title or not slug or not capacity_raw.isdecimal():
        return JsonResponse({"error": "Некоректні поля"}, status=400)
    capacity = int(capacity_raw)
    if capacity <= 0:
        return JsonResponse({"error": "Місткість має бути додатною"}, status=400)
    Course.objects.create(title=title, slug=slug,
                          capacity=capacity, status="draft")
    return redirect("courses:list")