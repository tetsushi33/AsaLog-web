from django.urls import path

from . import views

app_name = "logs"
urlpatterns = [
    path("", views.index, name="index"),
    # 既存: IDベース
    #path("<int:log_id>/", views.detail, name="detail"),
    #path("<int:log_id>/update/", views.update_log, name="update"),

    # 追加: 日付ベース（YYYYMMDD で受ける）
    path("<int:yyyymmdd>/", views.detail_by_date, name="detail_by_date"),
    path("<int:yyyymmdd>/update/", views.update_log_by_date, name="update_by_date"),
    path("<int:yyyymmdd>/delete/", views.delete_log_by_date, name="delete_by_date"),

    path("analyze/", views.analyze, name="analyze"),
    path("create/", views.create_log, name="create"),
    path("delete/<int:log_id>/", views.delete_log, name="delete"),
]