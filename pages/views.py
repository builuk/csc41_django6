from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse,JsonResponse, Http404,HttpResponseBadRequest
from django.views.decorators.http import require_POST
import json
def home(request):
    return HttpResponse("Hello World")

def hello(request):
    return HttpResponse("Hello")

def article(request, pk):
    if pk not in {1, 2, 3}:
        raise Http404("Статтю не знайдено")
    return HttpResponse(f"Стаття #{pk}")

def greet(request):
    name = request.GET.get("name", "гість")
    return HttpResponse(f"Привіт, {name}!")

@require_POST
def echo_json(request):
    try:
        data = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return HttpResponseBadRequest("Некоректний JSON")
    if not isinstance(data, dict):
        return HttpResponseBadRequest("Очікується JSON-об'єкт")
    return JsonResponse({"received": data})