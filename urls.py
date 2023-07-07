from django.urls import include, path, re_path
from onisite.plugins.admin_api import views


urlpatterns = [
  re_path(r'^/?$', views.description, name="admin_api_description"),
]
