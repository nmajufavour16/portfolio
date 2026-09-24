from django.contrib import admin
from .models import (
    AboutMe,
    BlogPost,
    Contact,
    ProjectImage,
    Projects,
    SiteSettings,
    Skills,
    Testimonials,
    Timeline,
)


class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1
    fields = ('image', 'stage', 'caption', 'order')


@admin.register(Projects)
class ProjectsAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'featured', 'order', 'created_at')
    list_filter = ('category', 'featured')
    search_fields = ('title', 'description', 'architecture_notes')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ProjectImageInline]


@admin.register(Skills)
class SkillsAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'proficiency', 'icon_slug')
    list_filter = ('category',)
    search_fields = ('name', 'category')


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_published', 'created_at', 'updated_at')
    list_filter = ('is_published',)
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Timeline)
class TimelineAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'date', 'end_date', 'location')
    list_filter = ('event_type',)
    search_fields = ('title', 'description', 'location')


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'submitted_at', 'is_read')
    list_filter = ('is_read', 'submitted_at')
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('submitted_at',)


@admin.register(AboutMe)
class AboutMeAdmin(admin.ModelAdmin):
    list_display = ('name', 'headline', 'available_for_work', 'location', 'email')


@admin.register(Testimonials)
class TestimonialsAdmin(admin.ModelAdmin):
    list_display = ('name', 'title', 'created_at')
    search_fields = ('name', 'title', 'testimonial')


@admin.register(ProjectImage)
class ProjectImageAdmin(admin.ModelAdmin):
    list_display = ('project', 'stage', 'caption', 'order')
    list_filter = ('stage',)


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'all_time_visitors')