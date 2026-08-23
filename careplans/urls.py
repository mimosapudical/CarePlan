from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("api/care-plans/", views.create_care_plan, name="create_care_plan"),
    path("api/care-plans/search/", views.search_care_plans, name="search_care_plans"),
    path("api/care-plans/<str:plan_id>/status/", views.get_care_plan_status, name="get_care_plan_status"),
    path("api/care-plans/<str:plan_id>/download/", views.download_care_plan, name="download_care_plan"),
    path("api/ops/care-plans/", views.get_ops_care_plans, name="get_ops_care_plans"),
    path("api/ops/care-plans/<str:plan_id>/retry/", views.retry_care_plan, name="retry_care_plan"),
    path("api/care-plans/<str:plan_id>/", views.get_care_plan, name="get_care_plan"),
]
