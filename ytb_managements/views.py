from django.shortcuts import render


def index(request):
    return render(request, 'ytb.html')
# Create your views here.
