# -*- coding: utf-8 -*-

import os
from member.conf import get_base_dir
from django.utils.translation import gettext_lazy as _

DEBUG = True
ROOT_URLCONF = 'member.urls'
LOGIN_URL = '/connexion'
LOGIN_REDIRECT_URL = "/"
STATIC_URL = '/static/'
MEDIA_URL = '/media/'
TEST_RUNNER = 'django.test.runner.DiscoverRunner'
CRISPY_TEMPLATE_PACK = "bootstrap"

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'oauth2_provider',
    'crispy_forms',
    'email_obfuscator',
    'member',
    'tests',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    'django.middleware.csrf.CsrfViewMiddleware',
    "django.contrib.messages.middleware.MessageMiddleware",
    'django.middleware.locale.LocaleMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    # Default context processors
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.request',
    'django.core.context_processors.tz',
    'django.contrib.messages.context_processors.messages',
)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

SITE_ID = 1
SECRET_KEY = "notasecret"

LANGUAGE_CODE = "en"
USE_I18N = True
USE_L10N = True
LOCALE_PATHS = (os.path.join(get_base_dir(), 'LOCALE'),)
LANGUAGES = (
    ('en', _('English')),
    ('fr', _('French')),
    ('es', _('Spanish')),
)
DEFAULT_LANGUAGE = 1

REST_FRAMEWORK = {
    # If the pagination isn't specify in the API, its configuration is
    # specified here.
    'PAGINATE_BY': 10,                 # Default to 10
    'PAGINATE_BY_PARAM': 'page_size',  # Allow client to override, using `?page_size=xxx`.
    'MAX_PAGINATE_BY': 100,             # Maximum limit allowed when using `?page_size=xxx`.
    # Active OAuth2 authentication.
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'oauth2_provider.ext.rest_framework.OAuth2Authentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework_xml.parsers.XMLParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework_xml.renderers.XMLRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': '60/hour',
        'user': '2000/hour'
    }
}

REST_FRAMEWORK_EXTENSIONS = {
    # If the cache isn't specify in the API, the time of the cache
    # is specified here in seconds.
    'DEFAULT_CACHE_RESPONSE_TIMEOUT': 60 * 15
}
