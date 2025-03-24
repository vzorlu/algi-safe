import os
from pathlib import Path
from datetime import timedelta
from django.utils.translation import gettext_lazy as _
from dotenv import load_dotenv
from .template import TEMPLATE_CONFIG, THEME_LAYOUT_DIR, THEME_VARIABLES

# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get("SECRET_KEY", default="")
DEBUG = True
ALLOWED_HOSTS = [
    "atasehir.algi.ai",
    "localhost",
    "127.0.0.1",
    "148.251.52.194",
    "95.216.211.228",  # Add the new IP address here
    "*",  # Optional: Allow all hosts (for development only - remove in production)
]
# Django Environment
ENVIRONMENT = os.environ.get("DJANGO_ENVIRONMENT", default="local")

# Static files settings
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Statik Dosya Dizinleri (Static File Directories)
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

# WhiteNoise settings - Adjusted for development
STATICFILES_STORAGE = (
    "django.contrib.staticfiles.storage.StaticFilesStorage"
    if DEBUG
    else "whitenoise.storage.CompressedStaticFilesStorage"
)
WHITENOISE_AUTOREFRESH = True  # Refresh static files when they change in development
WHITENOISE_USE_FINDERS = True  # Use Django's finders to locate static files in development
WHITENOISE_MAX_AGE = 0 if DEBUG else 31536000  # Don't cache in development mode

# Add static files finders for development
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

# WhiteNoise settings
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"
WHITENOISE_MAX_AGE = 31536000  # 1 year
WHITENOISE_AUTOREFRESH = DEBUG  # Only refresh in debug mode
WHITENOISE_USE_FINDERS = DEBUG  # Only use finders in debug mode

# Add whitenoise for static file serving
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Make sure this is second
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",  # Add this line
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.dashboards",
    "apps.layouts",
    "apps.front_pages",
    "apps.mail",
    "apps.chat",
    "apps.my_calendar",
    "apps.kanban",
    "apps.ecommerce",
    "apps.academy",
    "apps.logistics",
    "apps.invoice",
    "apps.users",
    "apps.access",
    "apps.pages",
    "apps.authentication",
    "apps.wizard_examples",
    "apps.modal_examples",
    "apps.cards",
    "apps.ui",
    "apps.extended_ui",
    "apps.icons",
    "apps.forms",
    "apps.form_layouts",
    "apps.form_wizard",
    "apps.form_validation",
    "apps.tables",
    "apps.charts",
    "apps.maps",
    "apps.transactions",
    "auth.apps.AuthConfig",
    "apps.containers",
    "apps.jobs",
    "apps.logs",
    "django_extensions",
    "rest_framework",
    "devices",
    "customer",
    "services",
    "channels",
    "channels.layers",
    "stream.apps.StreamConfig",
    "council",
    "import_export",
    "corsheaders",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "config.context_processors.language_code",
                "config.context_processors.my_setting",
                "config.context_processors.get_cookie",
                "config.context_processors.environment",
            ],
            "libraries": {
                "theme": "web_project.template_tags.theme",
            },
            "builtins": [
                "django.templatetags.static",
                "web_project.template_tags.theme",
            ],
        },
    },
]

# WSGI/ASGI Configuration
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

"""
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
"""

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGES = [
    ("tr", _("Turkish")),
    ("en", _("English")),
    ("fr", _("French")),
    ("ar", _("Arabic")),
    ("de", _("German")),
]

LANGUAGE_CODE = "tr"  # Set default language to Turkish

TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
LOCALE_PATHS = [BASE_DIR / "locale"]

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "src/assets"),  # Add this line to include src/assets directory
]

BASE_URL = os.environ.get("BASE_URL", default="http://192.168.1.9:8000")
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# OneSignal Bildirim Ayarlar��
ONESIGNAL_APP_ID = "0a1a5cc3-275b-4d55-9137-e6304c066af0"
ONESIGNAL_API_KEY = "MjgwNTU2YTQtZGE0MC00ZTc4LTg3MzktYTRlZmM0MzMzM2M4"

LOGIN_URL = "/login/"
LOGOUT_REDIRECT_URL = "/login/"

SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = 3600

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://atasehir.algi.ai",
    "https://atasehir.algi.ai",  # Add HTTPS version
    "http://148.251.52.194",
    "https://148.251.52.194",  # Add HTTPS version
    "http://95.216.211.228",  # Add HTTP version
    "https://95.216.211.228",  # Add HTTPS version
]

THEME_LAYOUT_DIR = THEME_LAYOUT_DIR
TEMPLATE_CONFIG = TEMPLATE_CONFIG
THEME_VARIABLES = THEME_VARIABLES

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ],
}

CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://atasehir.algi.ai",
    "https://atasehir.algi.ai",  # Add HTTPS version
    "http://148.251.52.194",
    "https://148.251.52.194",  # Add HTTPS version
    "https://api.mapbox.com",  # Add this line
    "http://95.216.211.228",  # Add HTTP version
    "https://95.216.211.228",  # Add HTTPS version
]

CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
}

# Channel Layers with fallback configuration
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
            "capacity": 1500,  # Channel layer capacity
            "expiry": 10,  # Message expiry in seconds
        },
        "OPTIONS": {
            "ssl_cert_reqs": None,  # Disable SSL certificate verification
            "retry_on_timeout": True,  # Retry on connection timeout
            "connection_retries": 3,  # Number of retries
            "connection_retry_delay": 0.5,  # Delay between retries in seconds
        },
    }
}

# Cache configuration with fallback to local memory cache
try:
    import redis

    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": "redis://127.0.0.1:6379/1",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "SOCKET_CONNECT_TIMEOUT": 5,
                "SOCKET_TIMEOUT": 5,
                "RETRY_ON_TIMEOUT": True,
                "MAX_CONNECTIONS": 1000,
                "CONNECTION_POOL_KWARGS": {"max_connections": 100},
            },
        }
    }
except (ImportError, redis.ConnectionError):
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "fallback-cache"}}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

# Security settings for development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

DATA_UPLOAD_MAX_NUMBER_FIELDS = 500000

# Import Export Settings
IMPORT_EXPORT_USE_TRANSACTIONS = True
IMPORT_EXPORT_SKIP_ADMIN_LOG = False
IMPORT_EXPORT_FORMATS = [
    "xlsx",
    "xls",
    "csv",
    "json",
]


# Email Settings
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"  # or your SMTP server
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")


TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")

TWILIO_WHATSAPP_NUMBER = os.environ.get("TWILIO_WHATSAPP_NUMBER")

CORS_ALLOW_ALL_ORIGINS = True  # Geliştirme için. Prodüksiyonda spesifik originler belirleyin
CORS_ALLOW_CREDENTIALS = True

MAPBOX_ACCESS_TOKEN = os.environ.get("MAPBOX_ACCESS_TOKEN", "")

# settings.py
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"

# User model configuration
AUTH_USER_MODEL = "auth.User"  # Add this line if using default Django User model

# Configure WhiteNoise for better performance
WHITENOISE_MAX_AGE = 31536000  # 1 year
WHITENOISE_AUTOREFRESH = False
WHITENOISE_USE_FINDERS = False
