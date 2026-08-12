import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
ENV_FILE = BASE_DIR / ".env"


def _load_env_file(path):
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env_file(ENV_FILE)

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-secret-key")
DEBUG = True
ALLOWED_HOSTS = ["*"]
ROOT_URLCONF = "careplan_mvp.urls"
WSGI_APPLICATION = "careplan_mvp.wsgi.application"

INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "rest_framework",
    "careplans",
]

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
    "careplans.exception_handler.AppExceptionMiddleware",
]

REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "careplans.exception_handler.exception_handler",
    "UNAUTHENTICATED_USER": None,
}

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [],
        },
    }
]

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

USE_SQLITE = os.environ.get("CAREPLAN_USE_SQLITE", "").strip().lower() in {"1", "true", "yes"}

if USE_SQLITE:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "test.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("POSTGRES_DB", "careplan"),
            "USER": os.environ.get("POSTGRES_USER", "careplan"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "careplan"),
            "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
            "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        }
    }

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CAREPLAN_QUEUE_NAME = os.environ.get("CAREPLAN_QUEUE_NAME", "careplan_queue")
CAREPLAN_EXECUTION_BACKEND = os.environ.get("CAREPLAN_EXECUTION_BACKEND", "celery")
CAREPLAN_K8S_NAMESPACE = os.environ.get("CAREPLAN_K8S_NAMESPACE", "default")
CAREPLAN_K8S_IMAGE = os.environ.get("CAREPLAN_K8S_IMAGE", "")
CAREPLAN_K8S_BACKOFF_LIMIT = int(os.environ.get("CAREPLAN_K8S_BACKOFF_LIMIT", "3"))

CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", REDIS_URL)
CELERY_TASK_TRACK_STARTED = True
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": LOG_DIR / "careplan.log",
            "formatter": "default",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
}
