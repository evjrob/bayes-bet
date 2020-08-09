"""
Django settings for bayesbet project.

Generated by 'django-admin startproject' using Django 2.2.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_PATH = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', '') != 'False'

ALLOWED_HOSTS = [
    'app',
    'bayesbet-prod-env.jhpvgkwv5v.us-east-1.elasticbeanstalk.com',
    'hockey.everettsprojects.com',
    'c0mvuqurzl.execute-api.us-east-1.amazonaws.com',
    'bayesbet.everettsprojects.com',
    'dev.bayesbet.everettsprojects.com'
    ]
if DEBUG is True:
    ALLOWED_HOSTS = ALLOWED_HOSTS + ['127.0.0.1']


# Application definition

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'django_s3_storage',
    'data.apps.DataConfig',
    'plots.apps.PlotsConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'bayesbet.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(SETTINGS_PATH, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'bayesbet.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {}
}

DATABASE_ROUTERS = []

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = []


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "static/")

STATICFILES_DIRS = [
   "plots/static",
   "bayesbet/static"
]

YOUR_S3_BUCKET = "bayes-bet-prod"

STATICFILES_STORAGE = "django_s3_storage.storage.StaticS3Storage"
AWS_S3_BUCKET_NAME_STATIC = YOUR_S3_BUCKET

# Serve the static files directly from the s3 bucket
AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % YOUR_S3_BUCKET
STATIC_URL = "https://%s/" % AWS_S3_CUSTOM_DOMAIN

# CORS HEADERS
CORS_ORIGIN_ALLOW_ALL = True
CORS_ORIGIN_WHITELIST = [
    "http://everettsprojects.com",
    "https://everettsprojects.com",
    "http://hockey.everettsprojects.com", 
    "https://hockey.everettsprojects.com", 
    "http://bayesbet-prod-env.jhpvgkwv5v.us-east-1.elasticbeanstalk.com",
    "http://c0mvuqurzl.execute-api.us-east-1.amazonaws.com",
    "http://bayesbet.everettsprojects.com",
    "https://bayesbet.everettsprojects.com",
    "http://dev.bayesbet.everettsprojects.com",
    "https://dev.bayesbet.everettsprojects.com"
    ]
if DEBUG is True:
    CORS_ORIGIN_WHITELIST = CORS_ORIGIN_WHITELIST + \
    ["http://localhost:8000", "http://127.0.0.1:8000", "file://*"]