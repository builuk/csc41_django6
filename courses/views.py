from django.http import HttpResponse
from .models import Course
from django.views.decorators.http import require_safe
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, render
from django.views import View
from .forms import CourseForm

# def course_list(request):
#     return HttpResponse("Список курсів EduHub")

# def course_create(request):
#     return HttpResponse("Форма створення курсу (демо)")

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
def course_json(request, pk):
    course = get_object_or_404(visible_courses(request.user), pk=pk)
    return JsonResponse({
        "id": course.pk,
        "title": course.title,
        "capacity": course.capacity,
    })

# @staff_member_required
# @require_http_methods(["POST"])
# def course_create(request):
#     title = request.POST.get("title", "").strip()
#     slug = request.POST.get("slug", "").strip()
#     capacity_raw = request.POST.get("capacity", "")
#     if not title or not slug or not capacity_raw.isdecimal():
#         return JsonResponse({"error": "Некоректні поля"}, status=400)
#     capacity = int(capacity_raw)
#     if capacity <= 0:
#         return JsonResponse({"error": "Місткість має бути додатною"}, status=400)
#     Course.objects.create(title=title, slug=slug,
#                           capacity=capacity, status="draft")
#     return redirect("courses:list")

# visible_courses(user) — наявна у проєкті функція
# вибірки лише тих курсів, які можна показувати user.

class CourseDetailView(View):
    http_method_names = ["get", "head", "options"]

    def get(self, request, pk):
        course = get_object_or_404(visible_courses(request.user), pk=pk)
        return render(request, "courses/detail.html", {"course": course})

class CourseListView(View):
    def get(self, request):
        courses = visible_courses(request.user).order_by("pk")
        return render(request, "courses/list.html", {"courses": courses})

class CourseJsonView(View):
    def get(self, request, pk):
        course = get_object_or_404(
            visible_courses(request.user), pk=pk
        )
        return JsonResponse({
            "id": course.pk,
            "title": course.title,
            "capacity": course.capacity,
        })


@require_safe
def course_detail(request, pk):
    course = get_object_or_404(visible_courses(request.user), pk=pk)
    return render(request, "courses/detail.html", {"course": course})


# @require_safe
# def course_list(request):
#     courses = visible_courses(request.user).order_by("pk")
#     return render(request, "courses/list.html", {"courses": courses})

@require_safe
def course_lessons(request, pk):
    course = get_object_or_404(visible_courses(request.user), pk=pk)
    lessons = course.lessons.order_by("position", "pk")
    return render(request, "courses/lessons.html", {
        "course": course,
        "lessons": lessons,
    })

def course_list(request):
    courses = Course.objects.order_by("id")
    return render(request, "courses/course_list.html", {"courses": courses})

def course_create(request):
    if request.method == "POST":
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("courses:list")
    else:
        form = CourseForm()
    return render(request, "courses/course_form.html", {"form": form})

def course_edit(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == "POST":
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            return redirect("courses:list")
    else:
        form = CourseForm(instance=course)
    return render(request, "courses/course_form.html", {"form": form, "course": course})
