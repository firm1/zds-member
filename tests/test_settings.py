from django.utils.http import urlquote

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
    'rest_framework_swagger',
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

