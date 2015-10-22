# coding: utf-8

from datetime import datetime
from member.conf import settings
from django.db import models
from hashlib import md5
from django.http import HttpRequest
from django.contrib.sessions.models import Session
from django.contrib.auth import logout
import os

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.dispatch import receiver
from django.contrib.sites.models import Site

import pygeoip
from .managers import ProfileManager
from importlib import import_module


class Profile(models.Model):
    """
    A user profile. Complementary data of standard Django `auth.user`.
    """

    class Meta:
        verbose_name = 'Profil'
        verbose_name_plural = 'Profils'
        permissions = (
            ("moderation", u"Moderate membre"),
            ("show_ip", u"Show member's Ip Adress"),
        )

    # Link with standard user is a simple one-to-one link, as recommended in official documentation.
    # See https://docs.djangoproject.com/en/1.6/topics/auth/customizing/#extending-the-existing-user-model
    user = models.OneToOneField(
        User,
        verbose_name='User',
        related_name="profile")

    last_ip_address = models.CharField(
        'IP Adress',
        max_length=39,
        blank=True,
        null=True)

    site = models.CharField('Web site', max_length=2000, blank=True)
    show_email = models.BooleanField('Show email adress on public',
                                     default=False)

    avatar_url = models.CharField(
        'Avatar url', max_length=2000, null=True, blank=True
    )

    biography = models.TextField('Biography', blank=True)

    karma = models.IntegerField('Karma', default=0)

    sign = models.TextField('Sign', max_length=250, blank=True)

    show_sign = models.BooleanField('Show signs', default=True)

    # TODO: Change this name. This is a boolean: "true" is "hover" or "click" ?!
    hover_or_click = models.BooleanField('Hover or clic ?', default=False)

    email_for_answer = models.BooleanField('Envoyer pour les réponse MP', default=False)

    can_read = models.BooleanField('Possibilité de lire', default=True)
    end_ban_read = models.DateTimeField(
        'Fin d\'interdiction de lecture',
        null=True,
        blank=True)

    can_write = models.BooleanField('Possibilité d\'écrire', default=True)
    end_ban_write = models.DateTimeField(
        'Fin d\'interdiction d\'ecrire',
        null=True,
        blank=True)

    last_visit = models.DateTimeField(
        'Date de dernière visite',
        null=True,
        blank=True)

    objects = ProfileManager()
    _permissions = {}

    def __unicode__(self):
        return self.user.username

    def is_private(self):
        """
        Check if the user belong to the bot's group or not

        :return: ``True`` if user belong to the bot's group, ``False`` else.

        :rtype: bool
        """
        user_groups = self.user.groups.all()
        user_group_names = [g.name for g in user_groups]
        return settings.ZDS_MEMBER['bot_group'] in user_group_names

    def get_absolute_url(self):
        """Absolute URL to the profile page."""
        return reverse('member-detail', kwargs={'user_name': self.user.username})

    def get_city(self):
        """
        Uses geo-localization to get physical localization of a profile through its last IP address.
        This works relatively good with IPv4 addresses (~city level), but is very imprecise with IPv6 or exotic internet
        providers.

        :return: The city and the country name of this profile.

        :rtype: str
        """
        # FIXME: this test to differentiate IPv4 and IPv6 addresses doesn't work, as IPv6 addresses may have length < 16
        # Example: localhost ("::1"). Real test: IPv4 addresses contains dots, IPv6 addresses contains columns.
        if len(self.last_ip_address) <= 16:
            gic = pygeoip.GeoIP(
                os.path.join(
                    settings.GEOIP_PATH,
                    'GeoLiteCity.dat'))
        else:
            gic = pygeoip.GeoIP(
                os.path.join(
                    settings.GEOIP_PATH,
                    'GeoLiteCityv6.dat'))

        geo = gic.record_by_addr(self.last_ip_address)

        if geo is not None:
            return u'{0}, {1}'.format(geo['city'], geo['country_name'])
        return ''

    def get_avatar_url(self):
        """Get the avatar URL for this profile.
        If the user has defined a custom URL, use it.
        If not, use Gravatar.

        :return: The avatar URL for this profile

        :rtype: str
        """
        if self.avatar_url:
            current_site = Site.objects.get_current()
            if self.avatar_url.startswith(settings.MEDIA_URL):
                return u"{}{}".format(current_site.domain, self.avatar_url)
            else:
                return self.avatar_url
        else:
            return 'https://secure.gravatar.com/avatar/{0}?d=identicon'.format(
                md5(self.user.email.lower().encode("utf-8")).hexdigest())

    def can_read_now(self):
        """
        Check if you can read a web site content as user.
        If you can't read, you can't login on website.
        This happens when you have been banned (temporarily or definitively)

        :return: ``False`` if you are banned, ``True`` else.

        :rtype: bool
        """
        if self.user.is_authenticated:
            if self.user.is_active:
                if self.end_ban_read:
                    return self.can_read or (
                        self.end_ban_read < datetime.now())
                else:
                    return self.can_read
            else:
                return False

    def can_write_now(self):
        """
        Check if you can write something on a web site as user.
        This happens when you have been reading only (temporarily or definitively)

        :return: ``False`` if you are read only, ``True`` else.

        :rtype: bool
        """
        if self.user.is_active:
            if self.end_ban_write:
                return self.can_write or (self.end_ban_write < datetime.now())
            else:
                return self.can_write
        else:
            return False


@receiver(models.signals.post_delete, sender=User)
def auto_delete_token_on_unregistering(sender, instance, **kwargs):
    """
    This signal receiver deletes forgotten password tokens and registering tokens for the un-registering user;
    """
    TokenForgotPassword.objects.filter(user=instance).delete()
    TokenRegister.objects.filter(user=instance).delete()


class TokenForgotPassword(models.Model):
    """
    When a user forgot its password, the website sends it an email with a token (embedded in a URL).
    If the user has the correct token, it can choose a new password on the dedicated page.
    This model stores the tokens for the users that have forgot their passwords, with an expiration date.
    """
    class Meta:
        verbose_name = 'Token de mot de passe oublié'
        verbose_name_plural = 'Tokens de mots de passe oubliés'

    user = models.ForeignKey(User, verbose_name='Utilisateur', db_index=True)
    token = models.CharField(max_length=100, db_index=True)
    date_end = models.DateTimeField('Date de fin')

    def get_absolute_url(self):
        """
        :return: The absolute URL of the "New password" page, including the correct token.
        """
        return reverse('member.views.new_password') + '?token={0}'.format(self.token)

    def __unicode__(self):
        return u"{0} - {1}".format(self.user.username, self.date_end)


class TokenRegister(models.Model):
    """
    On registration, a token is send by mail to the user. It must use this token (by clicking on a link) to activate its
    account (and prove the email address is correct) and connect itself.
    This model stores the registration token for each user, with an expiration date.
    """
    class Meta:
        verbose_name = 'Token d\'inscription'
        verbose_name_plural = 'Tokens  d\'inscription'

    user = models.ForeignKey(User, verbose_name='Utilisateur', db_index=True)
    token = models.CharField(max_length=100, db_index=True)
    date_end = models.DateTimeField('Date de fin')

    def get_absolute_url(self):
        """
        :return: the absolute URL of the account validation page, including the token.
        """
        return reverse('member.views.active_account') + '?token={0}'.format(self.token)

    def __unicode__(self):
        return u"{0} - {1}".format(self.user.username, self.date_end)


class Ban(models.Model):
    """
    This model stores all sanctions (not only bans).
    It stores sanctioned user, the moderator, the type of sanctions, the reason and the date.
    Note this stores also un-sanctions.
    """

    class Meta:
        verbose_name = 'Sanction'
        verbose_name_plural = 'Sanctions'

    user = models.ForeignKey(User, verbose_name='Sanctionné', db_index=True)
    moderator = models.ForeignKey(User, verbose_name='Moderateur',
                                  related_name='bans', db_index=True)
    type = models.CharField('Type', max_length=80, db_index=True)
    text = models.TextField('Explication de la sanction')
    pubdate = models.DateTimeField(
        'Date de publication',
        blank=True,
        null=True, db_index=True)

    def __unicode__(self):
        return u"{0} - ban : {1} ({2}) ".format(self.user.username, self.text, self.pubdate)


class KarmaNote(models.Model):
    """
    A karma note is a tool for staff to store data about a member.
    Data are:

    - A note (negative values are bad)
    - A comment about the member
    - A date

    This helps the staff to react and stores history of stupidities of a member.
    """
    class Meta:
        verbose_name = 'Note de karma'
        verbose_name_plural = 'Notes de karma'

    user = models.ForeignKey(User, related_name='karmanote_user', db_index=True)
    # TODO: coherence, "staff" is called "moderator" in Ban model.
    staff = models.ForeignKey(User, related_name='karmanote_staff', db_index=True)
    # TODO: coherence, "comment" is called "text" in Ban model.
    comment = models.CharField('Commentaire', max_length=150)
    value = models.IntegerField('Valeur')
    # TODO: coherence, "create_at" is called "pubdate" in Ban model.
    create_at = models.DateTimeField('Date d\'ajout', auto_now_add=True)

    def __unicode__(self):
        return u"{0} - note : {1} ({2}) ".format(self.user.username, self.comment, self.create_at)


def logout_user(username):
    """
    Logout the member.

    :param username: the name of the user to logout.
    """
    now = datetime.now()
    request = HttpRequest()

    sessions = Session.objects.filter(expire_date__gt=now)
    user = User.objects.get(username=username)

    for session in sessions:
        user_id = session.get_decoded().get('_auth_user_id')
        if user.id == user_id:
            engine = import_module(settings.SESSION_ENGINE)
            request.session = engine.SessionStore(session.session_key)
            logout(request)
            break
