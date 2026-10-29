from django.http import HttpResponse


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