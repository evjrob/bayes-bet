from django.urls import path, re_path

from . import views

urlpatterns = [
    re_path('^(staging|prod)?/?$', views.index, name='index'),
    re_path('^(staging|prod)?/?socialpreds$', views.social_preds)
]