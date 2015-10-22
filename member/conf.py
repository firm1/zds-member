import os
from django.utils.http import urlquote
from django.conf import settings as _settings  # noqa


def get_base_dir():
    return os.path.dirname(os.path.dirname(__file__))


DEFAULTS = {
    "BASE_DIR": get_base_dir(),
    "GEOIP_PATH": os.path.join(get_base_dir(), 'geodata'),
    "LOGIN_URL": '/connexion',
    "LOGIN_REDIRECT_URL": "/",
    "ABSOLUTE_URL_OVERRIDES": {
        'auth.user': lambda u: '/voir/{0}/'.format(urlquote(u.username.encode('utf-8')))
    },
    "CRISPY_TEMPLATE_PACK": "bootstrap",
    "TEMPLATE_DIRS": [
        # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
        # Always use forward slashes, even on Windows.
        # Don't forget to use absolute paths, not relative paths.
        os.path.join(get_base_dir(), 'templates')
    ],
    "ZDS_MEMBER": {
        'bot_account': "admin",
        'anonymous_account': "anonymous",
        'external_account': "external",
        'bot_group': 'bot',
        'members_per_page': 100,
    },
    "APP_SITE": {
        'name': u"ZesteDeSavoir",
        'litteral_name': u"Zeste de Savoir",
        'email_noreply': "noreply@example.com",
    },
    "ZDS_MEMBER_SETTINGS": {
        'paginator': {
            'folding_limit': 4
        }
    },
    "REST_FRAMEWORK": {
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
    },
    "REST_FRAMEWORK_EXTENSIONS": {
        # If the cache isn't specify in the API, the time of the cache
        # is specified here in seconds.
        'DEFAULT_CACHE_RESPONSE_TIMEOUT': 60 * 15
    },
    "CORS_ORIGIN_ALLOW_ALL": True,
    "CORS_ALLOW_METHODS": [
        'GET',
        'POST',
        'PUT',
        'DELETE',
    ],
    "CORS_ALLOW_HEADERS": [
        'x-requested-with',
        'content-type',
        'accept',
        'origin',
        'authorization',
        'x-csrftoken',
        'x-data-format'
    ]

}


class MemberSettings(object):
    '''
    Lazy Django settings wrapper for Django Member
    '''
    def __init__(self, wrapped_settings):
        self.wrapped_settings = wrapped_settings

    def __getattr__(self, name):
        if hasattr(self.wrapped_settings, name):
            return getattr(self.wrapped_settings, name)
        elif name in DEFAULTS:
            return DEFAULTS[name]
        else:
            raise AttributeError("'{}' setting not found".format(name))

settings = MemberSettings(_settings)
