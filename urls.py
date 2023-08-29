from django.urls import path, re_path
from onisite.plugins.admin_api import views


urlpatterns = [
  re_path(r'^$', views.summary, name="admin_api_summary"),
  path('batch/load', views.batch_load, name="admin_api_batch_load"),
  path('batch/purge', views.batch_purge, name="admin_api_batch_purge"),
  path('job/<str:job_id>/status', views.job_status, name="admin_api_job_status"),
]
