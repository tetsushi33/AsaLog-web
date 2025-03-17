from django.urls import path

from . import views

app_name = "logs"
urlpatterns = [
    path("", views.index, name="index"),
    path("<int:log_id>/", views.detail, name="detail"),
    path("<int:log_id>/update/", views.update_log, name="update"),
    path("analyze/", views.analyze, name="analyze"),
    path("create/", views.create_log, name="create"),
    path("delete/<int:log_id>/", views.delete_log, name="delete"),
]