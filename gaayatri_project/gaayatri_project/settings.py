import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
# Chatbot / external LLM settings
# Use environment variables (set in .env) to configure your Groq key and endpoint.
CHATBOT_PROVIDER = os.getenv('CHATBOT_PROVIDER', os.getenv('GROQ_PROVIDER', '')).lower() or None
CHATBOT_API_URL = os.getenv('CHATBOT_API_URL')  # optional; defaults to Groq chat completions URL in code
CHATBOT_API_KEY = os.getenv('CHATBOT_API_KEY') or os.getenv('GROQ_API_KEY')
CHATBOT_MODEL = os.getenv('CHATBOT_MODEL', '')  # optional; defaults to Groq llama-3.1-8b-instant in code
CHATBOT_EMBED_MODEL = os.getenv('CHATBOT_EMBED_MODEL', 'all-MiniLM-L6-v2')
HUGGINGFACE_API_TOKEN = os.getenv('HUGGINGFACE_API_TOKEN') or os.getenv('SENTENCE_TRANSFORMERS_API_KEY')
ALLOWED_SIMILARITY = float(os.getenv("ALLOWED_SIMILARITY", 0.65))
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'django-insecure-^#b5@8n63+t4bf+ddjq)(t#srf)egdam$av0)8hb^bcg=561*+'
DEBUG = True

ALLOWED_HOSTS = []

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'chatbot',
    'gaayatri_project',  # <--- CRITICAL: Make sure 'core' is added here
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'gaayatri_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [], # Django looks in app/templates automatically
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'gaayatri_project.wsgi.application'

# Database (Default SQLite)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation (Standard)
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'

# CRITICAL: This tells Django to use our custom User model in core/models.py
AUTH_USER_MODEL = 'core.User'

# Redirects after login/logout
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'