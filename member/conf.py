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
