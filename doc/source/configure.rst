=============
Configuration
=============

Configuration and list of available settings for zds-member

Specifying files
----------------

.. code:: python

    ZDS_MEMBER = {
            'bot_account': "admin",
            'anonymous_account': "anonymous",
            'external_account': "external",
            'bot_group': 'bot',
            'members_per_page': 100,
        }

    APP_SITE = {
            'name': u"ZesteDeSavoir",
            'litteral_name': u"Zeste de Savoir",
            'email_noreply': "noreply@example.com",
    }

    ZDS_MEMBER_SETTINGS = {
            'paginator': {
                'folding_limit': 4
            }
        }

Url
---

in ``url.py``

``(r'^members/', include('member.urls'))``

Templates
---------

A complete set of working templates is provided with the application. You may use it as it is with a CSS design of yours, re-use it or extend some parts of it.

Relations between templates:

.. code:: text

    base.html
    |_ member
    |  |_ base.html
    |  |_ index.html
    |  |_ login.html
    |  |_ profile.html
    |  |_ register
    |  |  |_ base.html
    |  |  |_ index.html
    |  |  |_ send_validation_email.html
    |  |  |_ send_validation_email_success.html
    |  |  |_ success.html
    |  |  |_ token_already_used.html
    |  |  |_ token_failed.html
    |  |  |_ token_success.html
    |  |_ settings
    |  |  |_ account.html
    |  |  |_ base.html
    |  |  |_ memberip.html
    |  |  |_ profile.html
    |  |  |_ promote.html
    |  |  |_  unregister.html
    |  |  |_  user.html
    |  |_ new_password
    |  |_ forgot_password
    |_ misc
    |  |_ badge.part.html
    |  |_ member_item.part.html
