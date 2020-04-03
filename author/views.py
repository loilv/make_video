from django.shortcuts import render
from django.views.generic import TemplateView


def login(request):
    return render(request, 'auth/login.html')

# Create your views here.
