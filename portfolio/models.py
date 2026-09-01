from django.db import models
from django.db.models.sql.constants import GET_ITERATOR_CHUNK_SIZE
from .utils import SIMPLE_ICON_SLUGS

# Create your models here.
class Skills(models.Model):
    name = models.CharField(max_length=100)
    proficiency = models.IntegerField()
    category = models.CharField(max_length=100)
    icon_slug = models.CharField(
        max_length=50, blank=True,
        help_text="Simple Icons slug (e.g. 'tailwindcss', 'react'). Leave blank to auto-detect from name."
    )
 
    def __str__(self):
        return self.name
 
    @property
    def resolved_icon_slug(self):
        return self.icon_slug or SIMPLE_ICON_SLUGS.get(self.name.strip().lower(), '')

class Projects(models.Model):
    class Category(models.TextChoices):
        FULLSTACK = 'Full Stack Development'
        DESIGN = 'Design'
        AI = 'AI Integration'
        
    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)
    category = models.CharField(max_length=50, choices=Category.choices, default=Category.FULLSTACK)
    thumbnail = models.ImageField(upload_to='projects/', blank=True, null=True)
    description = models.CharField(max_length=500)
    
    architecture_notes = models.TextField(blank=True, help_text='DEV: Problem, Architecture, Key Decisions. Leave blank for Design Projects.')
    design_role = models.CharField(max_length=100, blank=True, help_text="Design: e.g. 'Brand Identity, UI/UX'. Leave blank for DEV projects.")
    skills_used = models.ManyToManyField(Skills, related_name='projects', blank=True)
    featured = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0, help_text='Determines display order in the portfolio')

    github_url = models.URLField(max_length=200, blank=True, null=True)
    live_url = models.URLField(max_length=200, blank=True, null=True)
    canva_url = models.URLField(max_length=200, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    @property
    def is_design(self):
        return self.category == self.Category.DESIGN
    
class Timeline(models.Model):
    class EventType(models.TextChoices):
        EDUCATION = 'Education'
        EXPERIENCE = 'Experience'
        CERTIFICATION = 'Certification'
        LEADERSHIP = 'Leadership'
        

    event_type = models.CharField(max_length=50, choices=EventType.choices, default=EventType.EXPERIENCE)
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=200)
    date = models.DateField()
    end_date = models.DateField(null=True, blank=True, help_text="Leave blank if ongoing")
 
    credential_url = models.URLField(blank=True, null=True) 
    location = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        ordering = ['-date']
 
    def __str__(self):
        return self.title
    
class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    subject = models.CharField(max_length=200, blank=True, null=True)
    message = models.TextField()
    
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False, help_text='Mark as read when the message is read')
    
    class Meta:
        ordering = ['-submitted_at']
    
    def __str__(self):
        return self.name
    
class Testimonials(models.Model):
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=100)
    testimonial = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        
    def __str__(self):
        return self.name
    
class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, help_text="URL friendly name(e.g., how-i-built-waityr)")
    cover_image = models.ImageField(upload_to='covers/', blank=True, null=True)
    excerpt = models.CharField(max_length=200, blank=True, null=True)
    content = models.TextField()
    
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return self.title
    
    @property
    def reading_time(self):
        words = len(self.content.split())
        return max(1, words / 200)
    
class AboutMe(models.Model):
    name = models.CharField(max_length=100, default='Phayvo')
    headline = models.CharField(max_length=200, help_text='Full Stack Developer and Visual Designer')
    bio = models.TextField()
    available_for_work = models.BooleanField(default=True)

    profile_image = models.ImageField(upload_to='profile/')
    resume_pdf = models.FileField(upload_to='resume/', blank=True, null=True)
    
    github_username = models.CharField(max_length=100, blank=True, null=True)
    # Social Links
    github_link = models.URLField(max_length=100, blank=True, null=True)
    x_link = models.URLField(max_length=100, blank=True, null=True)
    linkedin_link = models.URLField(max_length=100, blank=True, null=True)
    instagram_link = models.URLField(max_length=100, blank=True, null=True)
    medium_link = models.URLField(max_length=100, blank=True, null=True)
    substack_link = models.URLField(max_length=100, blank=True, null=True)
    whatsapp_link = models.URLField(max_length=100, blank=True, null=True)
    pinterest_link = models.URLField(max_length=100, blank=True, null=True)
    
    class Meta:
        verbose_name_plural = "About Me"
        
    def __str__(self):
        return f"About: {self.name}"

class ProjectImage(models.Model):
    class Stage(models.TextChoices):
        PROCESS = 'PROC', 'Process'
        FINAL = 'FIN', 'Final'
 
    project = models.ForeignKey(Projects, related_name='gallery', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='projects/gallery/')
    stage = models.CharField(max_length=4, choices=Stage.choices, default=Stage.FINAL)
    caption = models.CharField(max_length=150, blank=True)
    order = models.PositiveIntegerField(default=0)
 
    class Meta:
        ordering = ['stage', 'order']
 
    def __str__(self):
        return f"{self.project.title} — {self.get_stage_display()} #{self.order}"