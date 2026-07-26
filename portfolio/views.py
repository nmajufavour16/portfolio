from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator

from .models import AboutMe, Contact, Skills, Projects, BlogPost, Testimonials, Timeline, ProjectImage
from .forms import ContactForm
from .utils import get_github_contributions

def home(request):
    about = AboutMe.objects.first()
    context = {
        'about': about,
        'feautured_projects': Projects.objects.filter(is_featured=True)[:4],
        'recents_posts': BlogPost.objects.filter(is_published=True)[:3],
        'testimonials': Testimonials.objects.all(),
        'contributions': (
            get_github_contributions(about.github_username)
            if about and about.github_username else None
        ),
    }
    return render(request, 'home.html', context)

def project_list_dev(request):
    projects = Projects.objects.exclude(category=Projects.Category.DESIGN)
    
    tech = request.GET.get('tech')
    if tech:
        projects = projects.filter(skills_name__name=tech)
    
    context = {
        'projects': projects.distinct(),
        'skills': Skills.objects.filter(projects__isnull=False).distinct(),
        'active_filter': tech,
    }
    
    if request.headers.get('HX-Request'):
        return render(request, 'partials/project_grid_dev.html', context)
    return render(request, 'project_list_dev.html', context)

def project_list_design(request):
    projects = Projects.objects.filter(category=Projects.Category.DESIGN)
    context = {'projects': projects}
    
    if request.headers.get('HX-Request'):
        return render(request, 'partials/project_grid_design.html', context)
    return render(request, 'project_list_design.html', context)

def project_detail(request, slug):
    project = get_object_or_404(
        Projects.objects.prefetch_related('gallery', 'skills_used'),
        slug=slug,
    )
    
    if project.is_design:
        context = {
            'project': project,
            'project_images': project.gallery.filter(stage=ProjectImage.Stage.PROCESS),
            'final_images': project.gallery.filter(stage=ProjectImage.Stage.FINAL),
        }
        
        return render(request, 'project_detail_design.html', context)
    return render(request, 'project_detail_dev.html', {'project': project})

def blog_list(request):
    posts = BlogPost.objects.filter(is_published=True).order_by('-published_date')
    paginator = Paginator(posts, 6)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'blog.html', {'page_obj': page_obj})

def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    return render(request, 'blog_detail.html', {'post': post})

def about(request):
    context = {
        'about': AboutMe.objects.first(),
        'timeline': Timeline.objects.all(),
    }
    return render(request, 'about.html', context)

def skills(request):
    all_skills = Skills.objects.all().order_by('category', '-proficiency')
    grouped = {}
    for skill in all_skills:
        grouped.setdefault(skill.category, []).append(skill)
    return render(request, 'skills.html', {'grouped_skills': grouped})

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Thank you for reaching out. I'll respond to your message as soon as I can.")
            return redirect('contact')
        else:
            messages.error(request, 'There was an error sending your message. Please try again.')
    else:
        form = ContactForm()
    return render(request, 'contact.html', {'form': form})