from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Segurança ──────────────────────────────────────────────────────────────────
SECRET_KEY = os.environ["SECRET_KEY"]
DEBUG = os.getenv("DEBUG", "False") == "True"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")

# ── Integrações externas ───────────────────────────────────────────────────────
VEXPENSES_TOKEN        = os.environ["VEXPENSES_TOKEN"]
CONTA_AZUL_CLIENT_ID   = os.environ["CONTA_AZUL_CLIENT_ID"]
CONTA_AZUL_CLIENT_SECRET = os.environ["CONTA_AZUL_CLIENT_SECRET"]

# ── Apps ───────────────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_filters",
    "corsheaders",
    "contaazulinfos",
    "vexpensesinfos",
    "dashboard",
]

# ── Middleware ─────────────────────────────────────────────────────────────────
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",   # serve estáticos em produção
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "uza.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "uza.wsgi.application"

# ── Banco de dados — Neon (PostgreSQL) ────────────────────────────────────────
DATABASES = {
    "default": dj_database_url.config(
        default=os.environ["DATABASE_URL"],
        conn_max_age=600,
        conn_health_checks=True,
        ssl_require=True,
    )
}

# ── CORS ───────────────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")

# ── Segurança HTTPS ────────────────────────────────────────────────────────────
SECURE_PROXY_SSL_HEADER    = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT         = not DEBUG
SESSION_COOKIE_SECURE       = not DEBUG
CSRF_COOKIE_SECURE          = not DEBUG
SECURE_HSTS_SECONDS         = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD         = not DEBUG

# ── Validação de senha ─────────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ── DRF ────────────────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"]
}

# ── Internacionalização ────────────────────────────────────────────────────────
LANGUAGE_CODE = "pt-br"
TIME_ZONE     = "America/Sao_Paulo"
USE_I18N      = True
USE_TZ        = True

# ── Arquivos estáticos ─────────────────────────────────────────────────────────
STATIC_URL  = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
