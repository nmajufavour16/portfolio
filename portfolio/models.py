from django.db import models
from django.db.models.sql.constants import GET_ITERATOR_CHUNK_SIZE

# Create your models here.
class Skills(models.fields.Model):
    name = models.CharField(max_length=100)
    proficiency = models.IntegerField()
    category = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Projects(models.Model):
    class Category(models.TextChoices):
        FULLSTACK = 'Full Stack Development'
        DESIGN = 'Design'
        AI = 'AI Integration'
        
    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)
    category = models.CharField(max_length=50, choices=Category.choices, default=Category.FULLSTACK)
    thumbnail = models.ImageField(upload_to='media/projects/')
    description = models.CharField(max_length=200)
    skills_used = models.ManyToManyField(Skills, related_name='projects')
    github_url = models.URLField(max_length=200, blank=True, null=True)
    live_url = models.URLField(max_length=200, blank=True, null=True)
    canva_url = models.URLField(max_length=200, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return self.title
    
class Timeline(models.Model):
    class EventType(models.TextChoices):
        EDUCATION = 'Education'
        EXPERIENCE = 'Experience'
        
    event_type = models.CharField(max_length=50, choices=EventType.choices, default=EventType.EXPERIENCE)
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=200)
    date = models.DateField()
    location = models.CharField(max_length=100)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
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
        ordering = ['submitted_at']
    
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
    cover_image = models.ImageField(upload_to='media/covers/', blank=True, null=True)
    content = models.TextField()
    
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return self.title
    
class AboutMe(models.Model):
    name = models.CharField(max_length=100, default='Phayvo')
    headline = models.CharField(max_length=200, help_text='Full Stack Developer and Visual Designer')
    bio = models.TextField()
    profile_image = models.ImageField(uploaded_to='/media/profile')
    resume_pdf = models.FileField(upload_to='/media/resume', blank=True, null=True)
    # Social Links
    github_link = models.URLField(max_length=100, blank=True, null=True)
    twitter_link = models.URLField(max_length=100, blank=True, null=True)
    linkedin_link = models.URLField(max_length=100, blank=True, null=True)
    instagram_link = models.URLField(max_length=100, blank=True, null=True)
    pinterest_link = models.URLField(max_length=100, blank=True, null=True)
    
    class Meta:
        verbose_name_plural = "About Me"
        
    def __str__(self):
        return f"About: {self.title}"
    