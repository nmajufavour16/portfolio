from datetime import date
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from .models import AboutMe, Skills, Projects, BlogPost, Timeline
from .utils import group_skills_by_category


@override_settings(
    STORAGES={
        'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
        'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
    }
)
class PortfolioViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.about = AboutMe.objects.create(
            name='Test User',
            headline='Full Stack Engineer',
            bio='Building robust software.',
            location='Lagos, Nigeria',
            available_for_work=True,
        )
        self.skill1 = Skills.objects.create(
            name='Python',
            category='Backend',
            proficiency=90,
        )
        self.skill2 = Skills.objects.create(
            name='React',
            category='Frontend',
            proficiency=85,
        )
        self.timeline = Timeline.objects.create(
            title='B.Sc in Computer Science',
            event_type=Timeline.EventType.EDUCATION,
            date=date(2022, 1, 1),
            description='Graduated with honors',
            location='Nigeria',
        )

    def test_home_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test User')

    def test_about_view(self):
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Behind the craft &amp; code')
        self.assertContains(response, 'Test User')
        self.assertContains(response, 'Full Stack Engineer')
        # Certifications section should NOT be rendered when empty
        self.assertNotContains(response, 'Certifications &amp; Credentials')
        self.assertNotContains(response, 'No certifications listed yet.')

    def test_skills_view(self):
        response = self.client.get(reverse('skills'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Python')
        self.assertContains(response, 'React')

    def test_projects_view(self):
        response = self.client.get(reverse('projects'))
        self.assertEqual(response.status_code, 200)

    def test_contact_get(self):
        response = self.client.get(reverse('contact'))
        self.assertEqual(response.status_code, 200)

    def test_resume_redirect_fallback(self):
        # When resume_pdf is not uploaded, redirects to about
        response = self.client.get(reverse('resume'))
        self.assertRedirects(response, reverse('about'))

    def test_testimonials_redirect(self):
        response = self.client.get(reverse('testimonials'))
        self.assertRedirects(response, reverse('home'))

    def test_blog_list_view(self):
        response = self.client.get(reverse('blog'))
        self.assertEqual(response.status_code, 200)

    def test_error_404_view(self):
        response = self.client.get(reverse('error_404'))
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'errors/404.html')
        self.assertContains(response, '404', status_code=404)
        self.assertContains(response, 'Lost in the void.', status_code=404)

    def test_error_500_view(self):
        response = self.client.get(reverse('error_500'))
        self.assertEqual(response.status_code, 500)
        self.assertTemplateUsed(response, 'errors/500.html')
        self.assertContains(response, '500', status_code=500)
        self.assertContains(response, 'System hiccup.', status_code=500)

    def test_error_403_view(self):
        response = self.client.get(reverse('error_403'))
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, 'errors/403.html')
        self.assertContains(response, '403', status_code=403)
        self.assertContains(response, 'Restricted territory.', status_code=403)

    def test_nonexistent_url_returns_404(self):
        response = self.client.get('/this-page-definitely-does-not-exist-12345/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'errors/404.html')


class PortfolioHelperAndModelTests(TestCase):
    def test_group_skills_by_category(self):
        s1 = Skills.objects.create(name='Django', category='Backend', proficiency=80)
        s2 = Skills.objects.create(name='Tailwind', category='Frontend', proficiency=85)
        grouped = group_skills_by_category(Skills.objects.all())
        self.assertIn('Backend', grouped)
        self.assertIn('Frontend', grouped)

    def test_blog_post_reading_time_is_int(self):
        post = BlogPost(
            title='Test Post',
            slug='test-post',
            content='word ' * 500,
        )
        self.assertIsInstance(post.reading_time, int)
        self.assertEqual(post.reading_time, 2)  # 500 / 200 rounded is 2

    def test_skills_resolved_icon_slug(self):
        skill = Skills(name='React', category='Frontend', proficiency=90)
        self.assertEqual(skill.resolved_icon_slug, 'react')


class SingleUserAdminSecurityTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        from django.contrib import admin
        from django.contrib.auth.models import User, Group

        self.User = get_user_model()
        self.admin_site = admin.site
        self.owner = self.User.objects.create_superuser(
            username='phayvo',
            email='phayvo@example.com',
            password='testpassword123',
        )
        self.other_user = self.User.objects.create_superuser(
            username='intruder',
            email='intruder@example.com',
            password='testpassword123',
        )

    def test_unauthenticated_admin_returns_404(self):
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 404)

    def test_admin_login_without_gate_key_returns_404(self):
        response = self.client.get('/admin/login/')
        self.assertEqual(response.status_code, 404)

    def test_admin_login_with_valid_gate_key_returns_200(self):
        from django.conf import settings
        gate_key = getattr(settings, 'ADMIN_GATE_KEY', 'phayvo')
        response = self.client.get(f'/admin/login/?key={gate_key}')
        self.assertEqual(response.status_code, 200)

    def test_user_and_group_models_are_unregistered(self):
        from django.contrib.auth.models import User, Group
        self.assertFalse(self.admin_site.is_registered(User))
        self.assertFalse(self.admin_site.is_registered(Group))

    def test_other_user_denied_admin_access(self):
        self.client.login(username='intruder', password='testpassword123')
        response = self.client.get('/admin/')
        # Non-owner user gets 404 or denied
        self.assertIn(response.status_code, [403, 404])

    def test_owner_granted_admin_access(self):
        self.client.login(username='phayvo', password='testpassword123')
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)

