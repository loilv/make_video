from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('create-video', views.create_video, name='create-video')
]