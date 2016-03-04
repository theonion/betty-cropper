import hashlib
import os
import os.path
import socket
import sys

import django
from django.conf.global_settings import *  # NOQA

socket.setdefaulttimeout(5)

DEBUG = False
TEMPLATE_DEBUG = False

ADMINS = ()

INTERNAL_IPS = ('127.0.0.1',)

MANAGERS = ADMINS

APPEND_SLASH = False

PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), os.pardir))

sys.path.insert(0, os.path.normpath(os.path.join(PROJECT_ROOT, os.pardir)))

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'betty.db',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

EMAIL_SUBJECT_PREFIX = '[Betty Cropper] '

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'UTC'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

USE_TZ = True

# Make this unique, and don't share it with anybody.
KEY_COMPONENT = ")*)&8a36)6%74e@-ne5(-!8a(vv#tkv()eyg&@0=zd^pl!7=y@".encode("utf-8")
SECRET_KEY = hashlib.md5(socket.gethostname().encode("utf-8") + KEY_COMPONENT).hexdigest()

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'betty.conf.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_ROOT, 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.staticfiles',

    'betty.cropper',
    'betty.authtoken',
    # 'betty.image_browser',
)

# Only use south with django < 1.7
if django.VERSION < (1, 7):
    INSTALLED_APPS = INSTALLED_APPS + ('south',)


CELERY_IGNORE_RESULT = True
CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
BROKER_URL = 'amqp://guest@127.0.0.1:5672//'

BETTY_STANDALONE_SERVER = True

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"

STATIC_ROOT = os.path.realpath(os.path.join(PROJECT_ROOT, 'static'))
STATIC_URL = '/static/'

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

# Doing this because we always want to upload to temp files.
FILE_UPLOAD_HANDLERS = ("django.core.files.uploadhandler.TemporaryFileUploadHandler",)
