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

PROJECT_ID_LIST = {
    "library": 2,
    "multimedia": 3,
    "data": 4,
    "seminarseries": 7,
    "ascus": 8,
    "mooc": 11,
    "staf": 14,
    "omat": 15,
    "platformu": 16,
    "islands": 17,
    "community": 18,
    "podcast": 3458,
}

PROJECT_LIST = {
    "library": { "id": 2, "url": "library/" },
    "multimedia": { "id": 3, "url": "multimedia/" },
    "data": { "id": 4, "url": "data/" },
    "seminarseries": { "id": 7, "url": "seminarseries/" },
    "ascus": { "id": 8, "url": "ascus/" },
    "mooc": { "id": 11, "url": "mooc/" },
    "staf": { "id": 14, "url": "staf/" },
    "omat": { "id": 15, "url": "omat/" },
    "platformu": { "id": 16, "url": "platformu/" },
    "islands": { "id": 17, "url": "islands/" },
    "community": { "id": 18, "url": "community/" },
    "podcast": { "id": 3458, "url": "podcast/" },
}

# Application definition

INSTALLED_APPS = [
    'core.apps.CoreConfig',
    'stafdb.apps.StafdbConfig',
    'library.apps.LibraryConfig',
    'multimedia.apps.MultimediaConfig',
    'data.apps.DataConfig',
    'seminarseries.apps.SeminarseriesConfig',
    'ascus.apps.AscusConfig',
    'mooc.apps.MoocConfig',
    'staf.apps.StafConfig',
    'omat.apps.OmatConfig',
    'platformu.apps.PlatformuConfig',
    'islands.apps.IslandsConfig',
    'community.apps.CommunityConfig',
    'podcast.apps.PodcastConfig',
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
]

# When importing data please deactivate the DebugToolbar, otherwise
# it will be even slower!
MIDDLEWARE = [
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.sites.middleware.CurrentSiteMiddleware',
]

CRON_CLASSES = [
    'core.crons.CreateMapJS',
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
