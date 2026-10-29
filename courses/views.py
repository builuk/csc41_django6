from django.http import HttpResponse


def course_list(request):
    return HttpResponse("Список курсів EduHub")


def course_create(request):
    return HttpResponse("Форма створення курсу (демо)")


def course_detail(request, pk):
    return HttpResponse(f"Курс #{pk}; тип: {type(pk).__name__}")