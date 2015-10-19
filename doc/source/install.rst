============
Installation
============

Install the development version::

    pip install zds-member

Add ``member`` to your ``INSTALLED_APPS`` setting::

    INSTALLED_APPS = (
        # ...
        "member",
        # ...
    )

See the list of :ref:`settings` to modify the default behavior of
zds-member and make adjustments for your website.

Add ``member.urls`` to your URLs definition::

    urlpatterns = patterns("",
        ...
        url(r"^members/", include("member.urls")),
        ...
    )


Once everything is in place make sure you run ``syncdb`` (Django 1.4 and 1.6)
or ``migrate`` (Django 1.7) to modify the database with the ``member`` app
models.

