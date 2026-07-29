from django.shortcuts import render
from .models import AboutMe

def site_info(request):
    global_about = AboutMe.objects.first()
    return {'global_about': global_about}