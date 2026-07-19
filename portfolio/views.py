from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import AboutMe, Contact, Skills, Projects, BlogPost, Testimonials, Timeline

# Create your views here.
def home(request):
    return render(request, 'home.html')

def projects(request):
    all_projects = Projects.objects.all()
    context = {
        'projects': all_projects
    }
    return render(request, 'projects.html', context)

def project_detail(request, slug):
    project = get_object_or_404(Projects, slug=slug)
    context = {
        'project': project
    }
    return render(request, 'project_detail.html', context)

def about(request):
    about_me = AboutMe.objects.first()
    timeline = Timeline.objects.all()
    context = {
        'about_me': about_me,
        'timeline': timeline
    }
    return render(request, 'about.html', context)

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        Contact.objects.create(name=name, email=email, subject=subject, message=message)
        messages.success(request, 'Thanks for reaching out. I will get back to you soon.')
        return redirect('contact')
    return render(request, 'contact.html')

def blog(request):
    posts = BlogPost.objects.all()
    context = {
        'posts': posts
    }
    return render(request, 'blog.html', context)

def blog_detail(request, slug):
    blog_post = get_object_or_404(BlogPost, slug=slug)
    context = {
        'blog_post': blog_post
    }
    return render(request, 'blog_detail.html', context)

def testimonials(request):
    all_testimonials = Testimonials.objects.all()
    context = {
        'testimonials': all_testimonials
    }
    return render(request, 'testimonials.html', context)
    
def skills(request):
    all_skills = Skills.objects.all()
    context = {
        'skills': all_skills
    }
    return render(request, 'skills.html', context)

def resume(request):
    return render(request, 'resume.html')

def error_404(request, exception):
    return render(request, '404.html', status=404)