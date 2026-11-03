from .settings import *

SECRET_KEY = 'isolated-tests-only-never-use-this-key-in-production'
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
ADMIN_USERNAME = 'phayvo'
ADMIN_GATE_KEY = 'test-admin-gate'
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
DEFAULT_FROM_EMAIL = 'owner@example.com'
GITHUB_TOKEN = None
SPOTIFY_CLIENT_ID = None
SPOTIFY_CLIENT_SECRET = None
SPOTIFY_REFRESH_TOKEN = None
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}
