from .models import AboutMe

def site_info(request):
    try:
        global_about = AboutMe.objects.first()
    except Exception:
        global_about = None
    return {'global_about': global_about}