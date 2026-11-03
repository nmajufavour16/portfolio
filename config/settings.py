import os
import dj_database_url
from pathlib import Path
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured
from urllib.parse import urlsplit

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').strip().lower() in {'1', 'true', 'yes', 'on'}
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', str(not DEBUG)).lower() == 'true'
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
# Enable only behind a proxy that strips and sets this header itself.
if os.environ.get('TRUST_PROXY_HTTPS') == '1':
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get('ALLOWED_HOSTS', '.vercel.app,127.0.0.1,localhost').split(',')
    if host.strip()
]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    #Third Party Apps
    'portfolio',
    'markdownify',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'portfolio.context_processors.site_info',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
DATABASE_URL = os.environ.get('DATABASE_URL', '').strip()
IS_LOCAL = os.environ.get('LOCAL') == '1'

if IS_LOCAL:
    DATABASE_URL = os.environ.get('LOCAL_DATABASE_URL', 'sqlite:///db.sqlite3')
else:
    DATABASE_URL = os.environ.get('DATABASE_URL', '')
    
# Check if the project is running on Vercel
IS_VERCEL = os.environ.get('VERCEL') == '1' or bool(os.environ.get('VERCEL_ENV'))

if DATABASE_URL:
    database_host = urlsplit(DATABASE_URL).hostname

    # A Vercel Function cannot reach a database running on the developer's
    # machine. Fail during startup with an actionable configuration error.
    if IS_VERCEL and database_host in {'localhost', '127.0.0.1', '::1'}:
        raise ImproperlyConfigured(
            'DATABASE_URL points to localhost. Configure a hosted PostgreSQL '
            'connection string in the Vercel project environment variables.'
        )

    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=0,
            conn_health_checks=True,
            disable_server_side_cursors=IS_VERCEL,
            ssl_require=IS_VERCEL,
        )
    }
elif IS_VERCEL:
    raise ImproperlyConfigured(
        'DATABASE_URL is required on Vercel. Connect a hosted PostgreSQL '
        'database and expose its connection string as DATABASE_URL.'
    )
else:
    # SQLite is a convenient local fallback, but is not durable on Vercel.
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Africa/Lagos'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
if os.environ.get('AWS_STORAGE_BUCKET_NAME'):
    STORAGES['default'] = {
        'BACKEND': 'storages.backends.s3.S3Storage',
        'OPTIONS': {
            'bucket_name': os.environ['AWS_STORAGE_BUCKET_NAME'],
            'region_name': os.environ.get('AWS_S3_REGION_NAME', 'us-east-1'),
            'endpoint_url': os.environ.get('AWS_S3_ENDPOINT_URL') or None,
            'default_acl': None,
            'file_overwrite': False,
        },
    }
elif IS_VERCEL:
    raise ImproperlyConfigured('Set AWS_STORAGE_BUCKET_NAME and S3 credentials for durable media on Vercel.')
else:
    MEDIA_ROOT = Path(os.environ.get('MEDIA_ROOT') or str(MEDIA_ROOT))
    MEDIA_URL = os.environ.get('MEDIA_URL') or MEDIA_URL

# Enable shared caching after migrations; local rendering needs no cache table.
USE_DATABASE_CACHE = os.environ.get('USE_DATABASE_CACHE') == '1'
CACHES = {
    'default': {
        'BACKEND': ('django.core.cache.backends.db.DatabaseCache' if USE_DATABASE_CACHE
                    else 'django.core.cache.backends.locmem.LocMemCache'),
        'LOCATION': 'portfolio_cache' if USE_DATABASE_CACHE else 'portfolio_integrations',
    }
}
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
SPOTIFY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REFRESH_TOKEN = os.environ.get('SPOTIFY_REFRESH_TOKEN')

# Single-User & Stealth Admin Gate Settings
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME') or 'phayvo'
ADMIN_GATE_KEY = os.environ.get('ADMIN_GATE_KEY', '')


# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_TIMEOUT = 10
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

MARKDOWNIFY = {
    "default": {
        "MARKDOWN_EXTENSIONS": [
            'markdown.extensions.extra',
            'markdown.extensions.nl2br',
        ],
        "WHITELIST_TAGS": [
            'a', 'abbr', 'acronym', 'b', 'blockquote', 'em', 'i', 'li', 'ol', 'p', 'strong', 'ul', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'code', 'pre', 'hr', 'img'
        ],
        "WHITELIST_ATTRS": [
            'href', 'src', 'alt', 'class', 'title'
        ]
    }
}
