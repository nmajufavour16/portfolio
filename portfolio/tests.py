from datetime import date
from unittest.mock import patch
import requests
from django.core.cache import cache
from django.core import mail
from django.core.management import call_command
from django.db import connection, IntegrityError, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, Client, TransactionTestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from .models import AboutMe, Skills, Projects, BlogPost, Timeline, ProjectImage, Contact
from .utils import group_skills_by_category, get_github_contributions, get_spotify_listening


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

    @patch('portfolio.views.get_github_contributions', return_value=None)
    @patch('portfolio.views.get_spotify_listening', return_value=None)
    def test_home_view(self, spotify, github):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test User')

    @patch('portfolio.views.get_spotify_listening', return_value=None)
    def test_about_view(self, spotify):
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

    def test_admin_index_with_valid_gate_key_redirects_and_renders_login(self):
        from django.conf import settings
        gate_key = getattr(settings, 'ADMIN_GATE_KEY', 'phayvo')
        response = self.client.get(f'/admin/?key={gate_key}', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Phayvo Studio')

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

    @override_settings(ADMIN_GATE_KEY='')
    def test_missing_gate_secret_does_not_unlock_login(self):
        self.assertEqual(self.client.get('/admin/login/?key=phayvo').status_code, 404)


class AuditRegressionTests(TestCase):
    def setUp(self):
        cache.clear()
        self.project = Projects.objects.create(
            title='A frontend project', slug='frontend', description='Example',
            category=Projects.Category.FRONTEND,
        )

    def test_optional_thumbnail_on_both_detail_templates(self):
        for category in (Projects.Category.FRONTEND, Projects.Category.DESIGN):
            with self.subTest(category=category):
                self.project.category = category
                self.project.save()
                response = self.client.get('/work/frontend/')
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, self.project.title)
                self.assertNotContains(response, '<img src=""')

    def test_duplicate_slug_is_rejected_by_database(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Projects.objects.create(title='Duplicate', slug='frontend', description='Example')

    def test_design_process_and_final_images_render(self):
        self.project.category = Projects.Category.DESIGN
        self.project.save()
        for stage, caption in ((ProjectImage.Stage.PROCESS, 'Process sketch'), (ProjectImage.Stage.FINAL, 'Final artwork')):
            ProjectImage.objects.create(project=self.project, image='projects/example.png', stage=stage, caption=caption)
        response = self.client.get('/work/frontend/')
        self.assertContains(response, 'Process sketch')
        self.assertContains(response, 'Final artwork')

    @patch('portfolio.views.get_github_contributions')
    @patch('portfolio.views.get_spotify_listening')
    def test_stats_render_in_initial_html_on_each_page_load(self, spotify, github):
        AboutMe.objects.create(name='Owner', headline='Developer', bio='Example', github_username='configured-owner')
        github.return_value = {
            'totalContributions': 1234, 'totalCommits': 500, 'totalRepos': 12,
            'currentStreak': 7, 'username': 'configured-owner',
            'profileUrl': 'https://github.com/configured-owner', 'weeks': [], 'monthLabels': [],
        }
        spotify.return_value = {
            'title': 'Example track', 'artist': 'Example artist', 'is_playing': True,
            'spotify_url': 'https://open.spotify.com/track/example',
        }
        Skills.objects.create(name='Python', category='Backend', proficiency=80)
        response = self.client.get('/')
        self.assertContains(response, 'data-target="1">1</span>')
        self.assertContains(response, 'href="/work/frontend/"')
        self.assertContains(response, "filter = 'Frontend Development'")
        self.assertContains(response, '1234')
        self.assertContains(response, 'Example track')
        self.assertContains(response, 'Example artist')
        self.assertContains(response, 'Currently listening')
        self.assertContains(response, 'https://github.com/configured-owner')
        self.assertNotContains(response, 'GitHub activity loads here')
        self.assertNotContains(response, 'hx-trigger="load')
        self.assertContains(response, 'hx-get="/spotify_status/"')
        self.assertContains(response, 'x-show="active === 0">')
        self.assertContains(response, 'width: 80%')
        github.return_value['totalContributions'] = 1235
        spotify.return_value['title'] = 'Next track'
        response = self.client.get('/')
        self.assertContains(response, '1235')
        self.assertContains(response, 'Next track')
        self.assertEqual(github.call_count, 2)
        github.assert_called_with('configured-owner')
        response = self.client.get('/about/')
        self.assertContains(response, 'Next track')
        self.assertEqual(spotify.call_count, 3)

    def test_htmx_filter_response_updates_selected_filter(self):
        skill = Skills.objects.create(name='React', category='Frontend', proficiency=85)
        self.project.skills_used.add(skill)
        design = Projects.objects.create(title='Design', slug='design', description='Example', category=Projects.Category.DESIGN)
        design.skills_used.add(skill)
        response = self.client.get('/work/development/?tech=React', HTTP_HX_REQUEST='true')
        self.assertContains(response, 'id="development-results"')
        self.assertContains(response, 'aria-current="true" class="tech-filter__pill is-active"')
        self.assertContains(response, 'React')
        self.assertContains(response, self.project.title)
        self.assertNotContains(response, '<html')

    def test_listing_prefetches_skills_in_one_query(self):
        skill = Skills.objects.create(name='Django', category='Backend', proficiency=90)
        self.project.skills_used.add(skill)
        for i in range(4):
            project = Projects.objects.create(title='Dev', slug=f'dev-{i}', description='Example')
            project.skills_used.add(skill)
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get('/work/development/')
        self.assertEqual(response.status_code, 200)
        # One prefetch query fetches skills for every project in the listing.
        self.assertEqual(sum(' IN (' in q['sql'] and '_prefetch_related_val_project' in q['sql'] for q in queries), 1)

    def test_contact_success_and_honeypot(self):
        payload = {'name': 'Visitor', 'email': 'visitor@example.com', 'subject': 'Project', 'message': 'Hello'}
        response = self.client.post('/contact/', payload)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Contact.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].reply_to, ['visitor@example.com'])
        response = self.client.post('/contact/', {**payload, 'website': 'spam.example'})
        self.assertEqual(Contact.objects.count(), 1)
        self.assertContains(response, "Please don&#x27;t try to spam me.")

    def test_contact_subject_error_is_visible_and_associated(self):
        response = self.client.post('/contact/', {'name': 'Visitor', 'email': 'visitor@example.com', 'subject': 'x' * 201, 'message': 'Hello'})
        self.assertContains(response, 'Ensure this value has at most 200 characters')
        self.assertContains(response, 'data-error-summary')
        self.assertContains(response, 'aria-describedby="id_subject_error"')
        self.assertContains(response, 'id="id_subject_error"')
        self.assertEqual(Contact.objects.count(), 0)

    @patch('portfolio.views.EmailMultiAlternatives.send', side_effect=OSError('SMTP unavailable'))
    def test_contact_is_saved_when_notification_fails(self, send):
        with self.assertLogs('portfolio.views', level='ERROR') as logs:
            response = self.client.post('/contact/', {'name': 'Visitor', 'email': 'visitor@example.com', 'message': 'Hello'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Contact.objects.count(), 1)
        self.assertIn('Contact notification failed for inquiry', logs.output[0])

    @override_settings(GITHUB_TOKEN='test-token')
    @patch('portfolio.utils.requests.post', side_effect=requests.Timeout('Unavailable'))
    def test_github_failure_serves_stale_data_and_backs_off(self, post):
        cache.set('github_contributions_example_stale', {'totalContributions': 12})
        with self.assertLogs('portfolio.utils', level='WARNING'):
            self.assertEqual(get_github_contributions('example')['totalContributions'], 12)
        self.assertEqual(get_github_contributions('example')['totalContributions'], 12)
        self.assertEqual(post.call_count, 1)

    @override_settings(SPOTIFY_CLIENT_ID='id', SPOTIFY_CLIENT_SECRET='secret', SPOTIFY_REFRESH_TOKEN='refresh')
    @patch('portfolio.utils.requests.post', side_effect=requests.Timeout('Unavailable'))
    def test_spotify_failure_backs_off(self, post):
        with self.assertLogs('portfolio.utils', level='WARNING'):
            self.assertIsNone(get_spotify_listening())
        self.assertIsNone(get_spotify_listening())
        self.assertEqual(post.call_count, 1)

    @patch('portfolio.views.get_github_contributions', return_value=None)
    @patch('portfolio.views.get_spotify_listening', return_value=None)
    def test_page_shows_fallbacks_when_services_are_unavailable(self, spotify, fetch):
        AboutMe.objects.create(name='Owner', headline='Developer', bio='Example', github_username='configured-owner')
        response = self.client.get('/')
        self.assertContains(response, 'https://github.com/configured-owner')
        self.assertContains(response, 'GitHub activity could not be refreshed right now.')
        self.assertContains(response, 'Spotify listening data is unavailable right now.')
        fetch.assert_called_once_with('configured-owner')

    @patch('portfolio.utils.requests.post')
    @patch('portfolio.utils.requests.get')
    def test_cached_integration_data_renders_without_external_calls(self, get, post):
        cache.set('github_contributions_nmajufavour16', {
            'totalContributions': 4321, 'totalCommits': 100, 'totalRepos': 5,
            'currentStreak': 3, 'username': 'nmajufavour16',
            'profileUrl': 'https://github.com/nmajufavour16',
        })
        cache.set('spotify_listening_now', {
            'title': 'Cached track', 'artist': 'Cached artist', 'is_playing': False,
        })
        response = self.client.get('/')
        self.assertContains(response, '4321')
        self.assertContains(response, 'Cached track')
        self.assertContains(response, 'Last listened')
        get.assert_not_called()
        post.assert_not_called()

    def test_models_match_migrations(self):
        call_command('makemigrations', check=True, dry_run=True, verbosity=0)

    def test_s3_media_generates_signed_urls_without_network(self):
        from storages.backends.s3 import S3Storage
        storage = S3Storage(bucket_name='portfolio-audit', access_key='test', secret_key='test',
                            region_name='us-east-1', signature_version='s3v4', file_overwrite=False)
        url = storage.url('projects/example.png')
        self.assertIn('projects/example.png', url)
        self.assertIn('X-Amz-Signature=', url)
        self.assertFalse(storage.file_overwrite)

    @override_settings(SECURE_SSL_REDIRECT=True, SESSION_COOKIE_SECURE=True, CSRF_COOKIE_SECURE=True)
    def test_https_redirect_and_secure_csrf_cookie(self):
        response = self.client.get('/contact/')
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, 'https://testserver/contact/')
        response = self.client.get('/contact/', secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.cookies['csrftoken']['secure'])


class ProjectSlugMigrationTests(TransactionTestCase):
    def test_duplicate_and_conflicting_slugs_preserve_every_project(self):
        executor = MigrationExecutor(connection)
        before = [('portfolio', '0008_aboutme_email_aboutme_location_aboutme_phone')]
        latest = executor.loader.graph.leaf_nodes()
        executor.migrate(before)
        try:
            Project = executor.loader.project_state(before).apps.get_model('portfolio', 'Projects')
            first = Project.objects.create(title='First', slug='shared', description='First')
            duplicate = Project.objects.create(title='Second', slug='shared', description='Second')
            Project.objects.create(title='Reserved', slug=f'shared-{duplicate.pk}', description='Reserved')
            executor = MigrationExecutor(connection)
            executor.migrate(latest)
            self.assertEqual(Projects.objects.count(), 3)
            self.assertEqual(Projects.objects.get(pk=first.pk).slug, 'shared')
            self.assertEqual(len(set(Projects.objects.values_list('slug', flat=True))), 3)
        finally:
            MigrationExecutor(connection).migrate(latest)

