from django.urls import path
from . import views

app_name = "pages"

urlpatterns = [
path('', views.home, name='home'),
path('hello/', views.hello, name='hello'),
path("articles/<int:pk>/", views.article, name="article"),
path("greet/", views.greet, name="greet"),
path("api/echo/", views.echo_json, name="echo")
    ]