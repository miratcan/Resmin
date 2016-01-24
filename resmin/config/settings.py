# -*- coding: utf-8 -*-

# Django settings for cb project.
import os
import sys
from datetime import timedelta
from django.utils.translation import ugettext_lazy as _


DEBUG = True
TEMPLATE_DEBUG = DEBUG
THUMBNAIL_DEBUG = DEBUG

ADMINS = (
    ('Mirat Can Bayrak', 'miratcanbayrak@gmail.com'),
)

MANAGERS = ADMINS

TIME_ZONE = 'Europe/Istanbul'
SITE_ID = 1

LANGUAGES = (
    ('en', _('English')),
    ('tr', _('Turkish')),
)

LANGUAGE_CODE = 'tr'

USE_I18N = True
USE_L10N = True
USE_TZ = False


EMAIL_HOST = "localhost"
EMAIL_FROM = "muduriyet@resm.in"
DEFAULT_FROM_EMAIL = EMAIL_FROM
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

PROJECT_ROOT = os.path.dirname(
    os.path.abspath(os.path.join(__file__.decode('utf-8'), '..', '..'))
)

sys.path.append(os.path.join(PROJECT_ROOT, 'resmin'))

STATIC_ROOT = os.path.join(PROJECT_ROOT, "static")
MEDIA_ROOT = os.path.join(PROJECT_ROOT, "media")

MEDIA_URL = "/media/"
STATIC_URL = "/static/"

STATICFILES_DIRS = (os.path.join(PROJECT_ROOT, "sitestatic/"), )

LOCALE_PATHS = [os.path.join(PROJECT_ROOT, "resmin", "locale/")]

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder'
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '^)pcn-k==)1nclfdrm$_6-q(fhh0q60niurvcygo$_a-mz5amt'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'pipeline.middleware.MinifyHTMLMiddleware',
)

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (os.path.join(PROJECT_ROOT, "resmin", "templates"), )

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'django.contrib.admin',

    'apps.question',
    'apps.account',
    'apps.follow',
    'apps.notification',
    'apps.story',
    'apps.comment',
    'apps.pm',

    'seo_cascade',
    'sorl.thumbnail',
    'pipeline',
    'json_field',
    'django_extensions',
    'rest_framework',
    'rosetta',
    'corsheaders',
    'hvad',
    'multilingual_tags',
    'widget_tweaks'
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.i18n",
    "django.contrib.messages.context_processors.messages",
    'django.core.context_processors.request',
    'apps.notification.context_processors.notifications'
)

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'resmin.log',
        },
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d '
                      '%(thread)d %(message)s'
        },
        'simple': {
            'format': '%(asctime)s %(levelname)s %(message)s'
        },
    },

    'loggers': {
        'django.request': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
    'loggers': {
        'notification': {
            'handlers': ['file'],
            'level': 'INFO',
            'formatter': 'simple'
        }
    }
}


AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

AUTH_PROFILE_MODULE = "account.UserProfile"

ABSOLUTE_URL_OVERRIDES = {
    'auth.user': lambda u: "/u/%s/" % u.username,
}

CACHES = {
    "default": {
        "BACKEND": "redis_cache.cache.RedisCache",
        "LOCATION": "127.0.0.1:6379:1",
        "OPTIONS": {
            "CLIENT_CLASS": "redis_cache.client.DefaultClient",
        }
    }
}

STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'

PIPELINE_CSS_COMPRESSOR = 'pipeline.compressors.yuglify.YuglifyCompressor'
PIPELINE_JS_COMPRESSOR = 'pipeline.compressors.yuglify.YuglifyCompressor'

PIPELINE_CSS = {
    'base': {
        'source_filenames': (
            'css/base.less',
        ),
        'output_filename': 'css/style.css',
        'extra_context': {
            'media': 'screen, projection',
        },
    },
}

PIPELINE_COMPILERS = (
    'pipeline.compilers.less.LessCompiler',
)


PIPELINE_JS = {
    'ga': {
        'source_filenames': (
            'js/ga.js',
        ),
        'output_filename': 'js/ga.js',
    }
}

BROKER_URL = 'redis://localhost:6379/0'

CELERYBEAT_SCHEDULE = {
    'publish_notifications': {
        'task': 'apps.notification.tasks.publish_notifications',
        'schedule': timedelta(seconds=60),
    },
}
AVATAR_QUESTIONMETA_ID = 1
DEFAULT_AVATAR_ANSWER_ID = 1

QUESTIONS_PER_PAGE = 40
STORIES_PER_PAGE = 20
COMMENTS_PER_PAGE = 50

ONLY_QUESTIONS_WITHOUT_ANSWERS_CAN_BE_DELETED = True
SEND_NOTIFICATION_EMAILS = False

INVITATION_KEY_LENGTH = 10
DEFAULT_INVITATION_USE_LIMIT = 20

FIXED_INVITATION_KEYS = []
EMAIL_TEMPLATES_PREFIX = 'emails'
CHUNKED_UPLOAD_PATH = '/upload/'
MAXIMUM_UPLOAD_SIZE = 6000000  # 6MB
UPLOAD_EXPIRATION_TIMEDELTA = timedelta(hours=6)  # 6Hours
PLAYBLE_MIME_TYPES = ['image/gif', 'video/webm', 'video/mp4']
FFMPEG_PATH = 'ffmpeg'
DEFAULT_VIDEO_THMB_URL = '%s%s' % (STATIC_URL, '/static/img/video_thmb.png')

# DJANGO REST FRAMEWORK SETTINGS
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ],
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    )
}

CORS_ORIGIN_ALLOW_ALL = True

try:
    from resmin.config.local_settings import *
except:
    pass
