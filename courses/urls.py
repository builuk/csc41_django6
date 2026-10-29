from django.urls import path
from . import views

app_name = "courses"

urlpatterns = [
    path("", views.course_list, name="list"),
    path("new/", views.course_create, name="create"),
    path("<int:pk>/", views.course_detail, name="detail"),
    path("search/", views.course_search, name="search"),
    path("slug/<slug:slug>/", views.course_by_slug, name="by-slug"),
]