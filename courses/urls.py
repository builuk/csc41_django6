from django.urls import path
from . import views
app_name = "courses"

urlpatterns = [
    path("", views.course_list, name="list"),
    path("cbv/", views.CourseListView.as_view(), name="list-cbv"),
    path("new/", views.course_create, name="create"),
    path("create/", views.course_create, name="create"),
    path("<int:pk>/", views.course_detail, name="detail"),
    path("<int:pk>/cbv/", views.CourseDetailView.as_view(), name="detail-cbv"),
    path("search/", views.course_search, name="search"),
    path("slug/<slug:slug>/", views.course_by_slug, name="by-slug"),
    path("<int:pk>/json/", views.course_json, name="json"),
    path("<int:pk>/json-cbv/", views.CourseJsonView.as_view(), name="json-cbv"),

]
