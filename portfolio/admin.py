from functools import update_wrapper
from types import MethodType
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import Group, User
from django.http import Http404
from django.shortcuts import redirect

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

# -----------------------------------------------------------------------------
# Single-User Restriction & Stealth Mode Gatekeeper
# -----------------------------------------------------------------------------
def single_user_has_permission(self, request):
    """
    Strictly permits only the designated single owner (superuser 'phayvo')
    to access the admin site. All other users (even if staff) are denied.
    """
    owner_username = getattr(settings, 'ADMIN_USERNAME')
    return bool(
        request.user
        and request.user.is_authenticated
        and request.user.is_active
        and request.user.is_superuser
        and request.user.username == owner_username
    )


def is_gate_unlocked(request):
    """
    Check if the request provides the stealth gate key via:
    1. Direct query parameter ?key=... or ?gate=...
    2. Embedded inside the 'next' parameter (e.g. ?next=/admin/?key=...)
    3. An already unlocked session flag.
    """
    gate_key = getattr(settings, 'ADMIN_GATE_KEY', 'phayvo')
    if not gate_key:
        return True

    # 1. Direct query parameter
    param_key = request.GET.get('key') or request.GET.get('gate')
    if param_key == gate_key:
        request.session['admin_gate_unlocked'] = True
        return True

    # 2. Key embedded in 'next' redirection parameter
    next_param = request.GET.get('next', '')
    if next_param and ('key=' in next_param or 'gate=' in next_param):
        from urllib.parse import urlparse, parse_qs
        parsed_qs = parse_qs(urlparse(next_param).query)
        next_key = (parsed_qs.get('key', [None])[0] or parsed_qs.get('gate', [None])[0])
        if next_key == gate_key:
            request.session['admin_gate_unlocked'] = True
            return True

    # 3. Session flag
    if request.session.get('admin_gate_unlocked') is True:
        return True

    return False


def stealth_admin_view(self, view, cacheable=False):
    """
    Wrap every admin view so that any unauthorized / unauthenticated request
    returns a 404 immediately without leaking any admin presence, unless the
    secret gate key is provided.
    """
    orig_wrapper = self._orig_admin_view(view, cacheable=cacheable)

    def inner(request, *args, **kwargs):
        if not self.has_permission(request):
            if request.user.is_authenticated:
                raise Http404("Page not found")
            if not is_gate_unlocked(request):
                raise Http404("Page not found")
        return orig_wrapper(request, *args, **kwargs)

    return update_wrapper(inner, view)


def stealth_login(self, request, extra_context=None):
    """
    Stealth Login:
    - If user is already authenticated as the owner, redirect to admin index.
    - If user is authenticated as anyone else, raise 404.
    - If user is unauthenticated, require the secret gate key (?key=<val> or ?gate=<val>
      or an already unlocked session or next redirect). Without the key, raise 404 so unauthorized
      visitors, bots, and crawlers see only 'Page Not Found'.
    """
    if request.user.is_authenticated:
        if self.has_permission(request):
            from django.urls import reverse
            return redirect(reverse('admin:index', current_app=self.name))
        raise Http404("Page not found")

    if not is_gate_unlocked(request):
        raise Http404("Page not found")

    return self._orig_login(request, extra_context=extra_context)


# Bind single-user and stealth logic to admin.site
if not hasattr(admin.site, '_orig_admin_view'):
    admin.site._orig_admin_view = admin.site.admin_view
if not hasattr(admin.site, '_orig_login'):
    admin.site._orig_login = admin.site.login

admin.site.admin_view = MethodType(stealth_admin_view, admin.site)
admin.site.has_permission = MethodType(single_user_has_permission, admin.site)
admin.site.login = MethodType(stealth_login, admin.site)

# Custom branding
admin.site.site_header = "Phayvo Studio"
admin.site.site_title = "Phayvo Admin"
admin.site.index_title = "Portfolio Management"


# Hide User and Group management from the Admin UI
if admin.site.is_registered(User):
    admin.site.unregister(User)
if admin.site.is_registered(Group):
    admin.site.unregister(Group)


# Portfolio Model Registrations
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