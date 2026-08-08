import os
from pathlib import Path
from dotenv import load_dotenv

# 1. Setup the true absolute path first
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. Force load_dotenv to look directly inside your main project root directory
ENV_PATH = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path=BASE_DIR / ".env")

GROQ_MODEL = "qwen/qwen3.6-27b"

STATIC_URL = "/static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",   # your dev static folder
]

STATIC_ROOT = BASE_DIR / "staticfiles"   # 👈 REQUIRED (fixes your error)

GOOGLE_CLIENT_ID = os.getenv("CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("CLIENT_SECRET")

# Read these safely from the environment
API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("API_URL")

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in product

ALLOWED_HOSTS = ["127.0.0.1","sabtco.com","www.sabbtco.com", "localhost","http://127.0.0.1:8000/google-one-tap/"]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Django default
    'django.contrib.sites',

    # allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    "django.contrib.sitemaps",
    'seo',
    'app.apps.AppConfig',

    
    # your apps...

    
]
SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",

    "django.middleware.locale.LocaleMiddleware",  # must be here

    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
   
    "allauth.account.middleware.AccountMiddleware",
]
ROOT_URLCONF = 'project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'app.context_processors.notification_count',
                'app.context_processors.google_client_id',

            ],
        },
    },
]

WSGI_APPLICATION = 'project.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
LOGIN_URL = "/login/"


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/6.0/topics/i18n/


from django.utils.translation import gettext_lazy as _

LANGUAGE_CODE = "en"

LANGUAGES = [
    ("en", _("English")),
    ("sw", _("Swahili")),
    ("de", _("German")),
    ("zh-hans", _("Chinese")),
]

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = TrueLANGUAGE_CODE = "en"

LANGUAGES = [
    ("en", _("English")),
    ("sw", _("Swahili")),
    ("de", _("German")),
    ("zh-hans", _("Chinese")),
]

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

LOGIN_URL = '/login/'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/
DEBUG = True

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "orders"   # optional


SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
    }
}

import os

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# project/settings.py

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'sammytings2@gmail.com'
# Use an App Password generated from Google Account Settings, NOT your normal login password
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD") 
#GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
 
DEFAULT_FROM_EMAIL = f'SABBTCo Logistics <{EMAIL_HOST_USER}>'
ADMIN_EMAIL = 'S@gmail.com'

ADMIN_PHONE = '+254727698319'
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": ["email", "profile"],
        "AUTH_PARAMS": {"access_type": "online"},
    }
}


#ACCOUNT_SIGNUP_FIELDS = ['email*']
SOCIALACCOUNT_ADAPTER = "app.adapters.MySocialAccountAdapter"

SOCIALACCOUNT_AUTO_SIGNUP = True
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_QUERY_EMAIL = True

# Automatically redirect authenticated users to your LOGIN_REDIRECT_URL 
# if they try to access login or signup pages
ACCOUNT_AUTHENTICATED_LOGIN_REDIRECTS = True

# Ensure your redirect URL is set to where you actually want them to go (e.g., a dashboard or home page)
  # Change 'home' to your specific URL name


LOGOUT_REDIRECT_URL = "index"
SOCIALACCOUNT_LOGIN_ON_GET = True

"yourapp.context_processors.active_banners"



STATIC_ROOT = BASE_DIR / "staticfiles"
