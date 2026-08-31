from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('work/', views.projects, name='projects'),
    path('work/development/', views.project_list_dev, name='project_list_dev'),
    path('work/design/', views.project_list_design, name='project_list_design'),
    path('work/<slug:slug>/', views.project_detail, name='project_detail'),
    path('contact/', views.contact, name='contact'),
    path('blog/', views.blog_list, name='blog'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog_detail'),
    path('testimonials/', views.testimonials, name='testimonials'),
    path('skills/', views.skills, name='skills'),
    path('resume/', views.resume, name='resume'),
    path('error_404/', views.error_404, name='error_404'),
]
