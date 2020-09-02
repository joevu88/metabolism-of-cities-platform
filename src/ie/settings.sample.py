"""
Django settings for ie project.

Generated by 'django-admin startproject' using Django 3.0.3.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '@h_n1ndpnw&***2yv6k%%bha%q&292hwydi^lk=obhsz5-s)b4'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['0.0.0.0', 'localhost']

SITE_ID = 1
SITE_EMAIL = 'info@metabolismofcities.org'

SENDGRID_API = 'SG.123123123'
TWITTER_API_ACCESS_TOKEN = '123123123'
TWITTER_API_ACCESS_TOKEN_SECRET = '123123123'
TWITTER_API_CONSUMER_KEY = '123123123'
TWITTER_API_CONSUMER_SECRET = '123123123'
FACEBOOK_ACCESS_TOKEN = '123123123'

LINKEDIN_API_ACCESS_TOKEN = "AQWK3cfYBPf7GsNQr1-PG1NXGZsKcVCLoNVz8o7j1e1U7LvZAQ6oLk4aZRp9ChHQpzvXqdiwMoU7cNDTUb6SWWjprePCW16NsJtvRGPzzqoyc3JSN1g_x9Vr1UgNMeyca97kaKYrFkdNHnXITCsveRTSiE33UXJPJcXu_caV0m_BBhRuVCXDfBPT3BH_Zu12IXpf9n8I7pJWC790ZVJo1TWmV_UUPNHpIFiyqIQnXwuKpIJjDI2v7l0tTqE9hBuGyDBvEhBzylCc___njboDxc-xQUYK8bjdM7qfcDrA13dZgoad3DrXHcdHU5MoG4d74enfw4RgzMEQQlg4isoEggJsdAxfsg"
EXPIRES_IN = 5183999
RAMDOM_STRING = "De9ZR5dsLsJScHFLAbAQz"
GEOAPIFY_API = "123123123"

PROJECT_ID_LIST = {
    "moc": 1,
    "core": 1,
    "library": 2,
    "multimedia": 3,
    "data": 4,
    "seminarseries": 7,
    "ascus": 8,
    "courses": 11,
    "staf": 14,
    "omat": 15,
    "platformu": 16,
    "islands": 17,
    "community": 18,
    "podcast": 3458,
    "stocks": 18683,
    "cityloops": 6,
    "untraceable": 32542,
}

RELATIONSHIP_ID_LIST = { 
    "author": 4,
    "uploader": 11,
    "participant": 12,
    "member": 6,
    "publisher": 2,
    "platformu_admin": 1,
}

PROJECT_LIST = {
    "library": { "id": 2, "url": "library/" },
    "multimedia": { "id": 3, "url": "multimedia/" },
    "data": { "id": 4, "url": "data/" },
    "seminarseries": { "id": 7, "url": "seminarseries/" },
    "ascus": { "id": 8, "url": "ascus/" },
    "courses": { "id": 11, "url": "courses/" },
    "staf": { "id": 14, "url": "staf/" },
    "omat": { "id": 15, "url": "omat/" },
    "platformu": { "id": 16, "url": "platformu/" },
    "islands": { "id": 17, "url": "islands/" },
    "community": { "id": 18, "url": "community/" },
    "podcast": { "id": 3458, "url": "podcast/" },
    "stocks": { "id": 18683, "url": "stocks/" },
    "cityloops": { "id": 6, "url": "cityloops/" },
    "untraceable": { "id": 32542, "url": "untraceable/" },
}

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'django_cron',
    'stdimage',
    'sass_processor',
    'django.contrib.sites',
    'bootstrap4',
    'tinymce',
    'anymail',
    'django.contrib.humanize',
#    'debug_toolbar',
    'channels',
]

# When importing data please deactivate the DebugToolbar, otherwise
# it will be even slower!
MIDDLEWARE = [
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',

    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',

    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.sites.middleware.CurrentSiteMiddleware',
]

X_FRAME_OPTIONS = 'SAMEORIGIN'

CRON_CLASSES = [
    'core.crons.CreateMapJS',
    'core.crons.EmailNotifications',
]

ROOT_URLCONF = 'ie.urls'

INTERNAL_IPS = [
    '172.28.0.1',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['./templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.site',
            ],
        },
    },
]

WSGI_APPLICATION = 'ie.wsgi.application'
ASGI_APPLICATION = 'core.routing.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('172.26.0.5', 6379)],
        },
    },
}


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'moc',
        'USER': 'postgres',
        'HOST': 'db',
        'PORT': 5432,
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = '/src/static/'
SASS_PROCESSOR_ROOT = STATIC_ROOT
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# Added for SASS: https://github.com/jrief/django-sass-processor
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'sass_processor.finders.CssFinder',
]

from django.contrib.messages import constants as messages

MESSAGE_TAGS = {
    messages.DEBUG: 'alert-info',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}

ANYMAIL = {
    "SENDGRID_API_KEY": SENDGRID_API,
}
#EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = '/src/logs/mail.log'
DEFAULT_FROM_EMAIL = "info@metabolismofcities.org"
SERVER_EMAIL = "info@metabolismofcities.org"

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/src/logs/django_cache',
    }
}

SESSION_COOKIE_DOMAIN=".metabolismofcities.org"
