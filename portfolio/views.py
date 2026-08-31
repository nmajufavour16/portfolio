from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone


from .models import AboutMe, Contact, Skills, Projects, BlogPost, Testimonials, Timeline, ProjectImage
from .forms import ContactForm
from .utils import (
    get_github_contributions,
    get_spotify_listening,
    get_tech_icons,
    get_visit_count,
    group_skills_by_category,
)

def home(request):
    about = AboutMe.objects.first()
    projects = Projects.objects.prefetch_related('skills_used', 'gallery')
    skills = Skills.objects.all().order_by('category', '-proficiency')
    first_milestone = Timeline.objects.order_by('date').first()
    github_username = 'nmajufavour16'
    context = {
        'about': about,
        'projects' : projects,
        'featured_projects': projects.filter(featured=True)[:4],
        'recent_posts': BlogPost.objects.filter(is_published=True)[:3],
        'testimonials': Testimonials.objects.all(),
        'contributions': get_github_contributions(github_username),
        'spotify': get_spotify_listening(),
        'github_username': github_username,
        'expertise_groups': group_skills_by_category(skills),
        'tech_icons': get_tech_icons(skills),
        'total_skills': skills.count(),
        'total_projects': projects.count(),
        'visit_count': get_visit_count(),
        'years_experience': (
            max(0, timezone.now().year - first_milestone.date.year)
            if first_milestone else 0
        ),
    }
    return render(request, 'home.html', context)


def projects(request):
    all_projects = Projects.objects.prefetch_related('skills_used', 'gallery')
    return render(request, 'projects.html', {
        'development_projects': all_projects.exclude(category=Projects.Category.DESIGN),
        'design_projects': all_projects.filter(category=Projects.Category.DESIGN),
    })

def project_list_dev(request):
    projects = Projects.objects.exclude(category=Projects.Category.DESIGN)
    
    tech = request.GET.get('tech')
    if tech:
        projects = projects.filter(skills_used__name=tech)
    
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
    posts = BlogPost.objects.filter(is_published=True).order_by('-created_at')
    paginator = Paginator(posts, 6)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'blog.html', {'page_obj': page_obj})

def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    return render(request, 'blog_detail.html', {'post': post})

def about(request):
    context = {
        'about': AboutMe.objects.first(),
        'certifications': Timeline.objects.filter(event_type=Timeline.EventType.CERTIFICATION),
        'story_milestones': Timeline.objects.exclude(event_type=Timeline.EventType.CERTIFICATION),
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

def testimonials(request):
    context = {'testimonials' : testimonials}
    return render(request, context)

def resume(request):
    context = {'resume' : resume}
    return render(request, context)

def error_404(request):
    return render(request, 'error_404.html')
