from django.urls import path, re_path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('socialpreds', views.social_preds),
    path('socialpreds/ready', views.social_preds_ready)
]