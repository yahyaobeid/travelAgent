import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - fails fast if dependency missing
    load_dotenv = None

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

if load_dotenv:
    load_dotenv(BASE_DIR.parent / ".env")


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("DJANGO_SECRET")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

ALLOWED_HOSTS = [
    "triphelix.com",
    "www.triphelix.com",
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    ".replit.dev",
    ".replit.app",
    ".repl.co",
]

_REPLIT_DOMAIN = os.getenv("REPLIT_DEV_DOMAIN", "")
if _REPLIT_DOMAIN:
    ALLOWED_HOSTS.append(_REPLIT_DOMAIN)

CSRF_TRUSTED_ORIGINS = [
    "https://triphelix.com",
    "https://www.triphelix.com",
    "https://*.replit.dev",
    "https://*.replit.app",
    "https://*.repl.co",
]
if _REPLIT_DOMAIN:
    CSRF_TRUSTED_ORIGINS.append(f"https://{_REPLIT_DOMAIN}")

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "core",
    "itinerary",
    "flights",
    "cars",
    "users",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
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
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", os.getenv("PGDATABASE", "triphelix")),
        "USER": os.getenv("POSTGRES_USER", os.getenv("PGUSER", "default")),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", os.getenv("PGPASSWORD", "password")),
        "HOST": os.getenv("POSTGRES_HOST", os.getenv("PGHOST", "localhost")),
        "PORT": os.getenv("POSTGRES_PORT", os.getenv("PGPORT", "5432")),
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/
STATIC_URL = "static/"
STATICFILES_DIRS = [
    BASE_DIR.parent / "static",
    BASE_DIR.parent / "frontend" / "dist",
]
STATIC_ROOT = BASE_DIR / "staticfiles"

if not DEBUG:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# React SPA — path to the built index.html served by the catch-all view
REACT_INDEX_HTML = BASE_DIR.parent / "frontend" / "dist" / "index.html"

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_REDIRECT_URL = "core:home"
LOGOUT_REDIRECT_URL = "users:login"
LOGIN_URL = "users:login"

# CORS — allow Vite dev server and Replit proxy in development
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5000",
    "http://0.0.0.0:5000",
]
if _REPLIT_DOMAIN:
    CORS_ALLOWED_ORIGINS.append(f"https://{_REPLIT_DOMAIN}")
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOW_CREDENTIALS = True

# CSRF — allow the React SPA to read the token from the cookie
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SAMESITE = "Lax"

# DRF — session auth + JSON renderer by default
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_DESTINATION_MODEL = os.getenv("OPENAI_DESTINATION_MODEL", "gpt-4o-mini")
TICKETMASTER_API_KEY = os.getenv("TICKETMASTER_API_KEY")


# Logging configuration to capture full outbound/inbound API I/O
# In production (e.g., EC2 with DEBUG=false), default to ERROR-only logging unless overridden
LOG_LEVEL = "DEBUG" if DEBUG else os.getenv("DJANGO_LOG_LEVEL", "ERROR")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(asctime)s %(levelname)s [%(name)s] %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "level": LOG_LEVEL,
        },
        "api_file": {
            "class": "logging.FileHandler",
            "formatter": "verbose",
            "level": LOG_LEVEL,
            "filename": str(BASE_DIR / "api.log"),
            "encoding": "utf-8",
        },
    },
    "loggers": {
        # Project apps
        "core": {"handlers": ["console", "api_file"], "level": LOG_LEVEL, "propagate": True},
        "itinerary": {"handlers": ["console", "api_file"], "level": LOG_LEVEL, "propagate": True},
        "itinerary.services": {"handlers": ["console", "api_file"], "level": LOG_LEVEL, "propagate": False},
        "itinerary.eventbrite": {"handlers": ["console", "api_file"], "level": LOG_LEVEL, "propagate": False},
        "flights": {"handlers": ["console", "api_file"], "level": LOG_LEVEL, "propagate": True},
        "flights.nl_search": {"handlers": ["console", "api_file"], "level": LOG_LEVEL, "propagate": False},
        "cars": {"handlers": ["console", "api_file"], "level": LOG_LEVEL, "propagate": True},
        "cars.services": {"handlers": ["console", "api_file"], "level": LOG_LEVEL, "propagate": False},

        # Third-party HTTP clients
        "openai": {"handlers": ["console", "api_file"], "level": LOG_LEVEL, "propagate": False},
        "httpx": {"handlers": ["console", "api_file"], "level": LOG_LEVEL, "propagate": False},
        "urllib3": {"handlers": ["console", "api_file"], "level": LOG_LEVEL, "propagate": False},
        "requests": {"handlers": ["console", "api_file"], "level": LOG_LEVEL, "propagate": False},
    },
}
