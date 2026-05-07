"""
Django settings for uza project.
"""

from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-4#2u1f)fej4)0g*hl7)#7hog1glccu(#-gn47ve3yyo-!1*5pd'

DEBUG = True

ALLOWED_HOSTS = ['*']

# ── Credenciais externas ───────────────────────────────────────────────────────

VEXPENSES_TOKEN = 'v4RNRlSmtvFV897mfOdIxLLzAkODTRlZyEiDaf2y2OQb3N59QL2O4bHOsgCC'

CONTA_AZUL_CLIENT_ID = 'mqtj80lnr02olc4m9be48jo9g'
CONTA_AZUL_CLIENT_SECRET = '1hkcaftg0fvlud38tb9biqtpful9sdbuhj4h6jttbf65efmk184g'

# ── Apps ───────────────────────────────────────────────────────────────────────

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django_filters',
    'corsheaders',
    'contaazulinfos',
    'vexpensesinfos',
    'dashboard',
]

# ── Middleware ─────────────────────────────────────────────────────────────────

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',          # deve ser o primeiro
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ── CORS ───────────────────────────────────────────────────────────────────────

CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',   # Vite dev server (padrão)
    'http://localhost:3000',   # fallback React
    'http://127.0.0.1:5173',
    'http://127.0.0.1:3000',
    'http://127.0.0.1:8000',
]

# ── URLs ───────────────────────────────────────────────────────────────────────

ROOT_URLCONF = 'uza.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'uza.wsgi.application'

# ── Banco de dados ─────────────────────────────────────────────────────────────
"""
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
"""

WSGI_APPLICATION = "uza.wsgi.application"

# ── Banco de dados — Neon (PostgreSQL) ────────────────────────────────────────
DATABASES = {
    "default": dj_database_url.config(
        #default=os.environ["DATABASE_URL"],
        default="postgresql://neondb_owner:npg_Aut3lsbJdy0L@ep-curly-king-aqbkka6u.c-8.us-east-1.aws.neon.tech/neondb?sslmode=require",
        conn_max_age=600,
        conn_health_checks=True,
        ssl_require=True,
    )
}

# ── Validação de senha ─────────────────────────────────────────────────────────

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── DRF ────────────────────────────────────────────────────────────────────────

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend']
}

# ── Internacionalização ────────────────────────────────────────────────────────

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True

USE_TZ = True

# ── Arquivos estáticos ─────────────────────────────────────────────────────────

STATIC_URL = 'static/'