from django.urls import path

from .views import login_user, index


urlpatterns = [
    path('', index, name='index'),
    path('login', login_user, name='login_user')
]