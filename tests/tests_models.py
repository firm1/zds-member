# coding: utf-8

import os
import shutil

from datetime import datetime, timedelta

from member.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from django.contrib.auth.models import Group
from hashlib import md5

from member.factories import ProfileFactory, StaffProfileFactory
from member.models import TokenForgotPassword, TokenRegister, Profile


BASE_DIR = settings.BASE_DIR


@override_settings(MEDIA_ROOT=os.path.join(BASE_DIR, 'media-test'))
class MemberModelsTest(TestCase):

    def setUp(self):
        self.user1 = ProfileFactory()
        self.staff = StaffProfileFactory()

    def test_unicode_of_username(self):
        self.assertEqual(self.user1.__unicode__(), self.user1.user.username)

    def test_get_absolute_url_for_details_of_member(self):
        self.assertEqual(self.user1.get_absolute_url(), '/voir/{0}/'.format(self.user1.user.username))

    def test_get_avatar_url(self):
        # if no url was specified -> gravatar !
        self.assertEqual(self.user1.get_avatar_url(),
                         'https://secure.gravatar.com/avatar/{0}?d=identicon'.
                         format(md5(self.user1.user.email.lower()).hexdigest()))
        # if an url is specified -> take it !
        user2 = ProfileFactory()
        testurl = 'http://test.com/avatar.jpg'
        user2.avatar_url = testurl
        self.assertEqual(user2.get_avatar_url(), testurl)

    def test_can_read_now(self):
        self.user1.user.is_active = False
        self.assertFalse(self.user1.can_write_now())
        self.user1.user.is_active = True
        self.assertTrue(self.user1.can_write_now())
        # TODO Some conditions still need to be tested

    def test_can_write_now(self):
        self.user1.user.is_active = False
        self.assertFalse(self.user1.can_write_now())
        self.user1.user.is_active = True
        self.assertTrue(self.user1.can_write_now())
        # TODO Some conditions still need to be tested

    def test_get_city_with_wrong_ip(self):
        # Set a local IP to the user
        self.user1.last_ip_address = '127.0.0.1'
        # Then the get_city is not found and return empty string
        self.assertEqual('', self.user1.get_city())

        # Same goes for IPV6
        # Set a local IP to the user
        self.user1.last_ip_address = '0000:0000:0000:0000:0000:0000:0000:0001'
        # Then the get_city is not found and return empty string
        self.assertEqual('', self.user1.get_city())

    def test_reachable_manager(self):
        # profile types
        profile_normal = ProfileFactory()
        profile_superuser = ProfileFactory()
        profile_superuser.user.is_superuser = True
        profile_superuser.user.save()
        profile_inactive = ProfileFactory()
        profile_inactive.user.is_active = False
        profile_inactive.user.save()
        profile_bot = ProfileFactory()
        profile_bot.user.username = settings.ZDS_MEMBER["bot_account"]
        profile_bot.user.save()
        profile_anonymous = ProfileFactory()
        profile_anonymous.user.username = settings.ZDS_MEMBER["anonymous_account"]
        profile_anonymous.user.save()
        profile_external = ProfileFactory()
        profile_external.user.username = settings.ZDS_MEMBER["external_account"]
        profile_external.user.save()
        profile_ban_def = ProfileFactory()
        profile_ban_def.can_read = False
        profile_ban_def.can_write = False
        profile_ban_def.save()
        profile_ban_temp = ProfileFactory()
        profile_ban_temp.can_read = False
        profile_ban_temp.can_write = False
        profile_ban_temp.end_ban_read = datetime.now() + timedelta(days=1)
        profile_ban_temp.save()
        profile_unban = ProfileFactory()
        profile_unban.can_read = False
        profile_unban.can_write = False
        profile_unban.end_ban_read = datetime.now() - timedelta(days=1)
        profile_unban.save()
        profile_ls_def = ProfileFactory()
        profile_ls_def.can_write = False
        profile_ls_def.save()
        profile_ls_temp = ProfileFactory()
        profile_ls_temp.can_write = False
        profile_ls_temp.end_ban_write = datetime.now() + timedelta(days=1)
        profile_ls_temp.save()

        # groups

        bot = Group(name=settings.ZDS_MEMBER["bot_group"])
        bot.save()

        # associate account to groups
        bot.user_set.add(profile_anonymous.user)
        bot.user_set.add(profile_external.user)
        bot.user_set.add(profile_bot.user)
        bot.save()

        # test reachable user
        profiles_reacheable = Profile.objects.contactable_members().all()
        self.assertIn(profile_normal, profiles_reacheable)
        self.assertIn(profile_superuser, profiles_reacheable)
        self.assertNotIn(profile_inactive, profiles_reacheable)
        self.assertNotIn(profile_anonymous, profiles_reacheable)
        self.assertNotIn(profile_external, profiles_reacheable)
        self.assertNotIn(profile_bot, profiles_reacheable)
        self.assertIn(profile_unban, profiles_reacheable)
        self.assertNotIn(profile_ban_def, profiles_reacheable)
        self.assertNotIn(profile_ban_temp, profiles_reacheable)
        self.assertIn(profile_ls_def, profiles_reacheable)
        self.assertIn(profile_ls_temp, profiles_reacheable)

    def tearDown(self):
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)


class TestTokenForgotPassword(TestCase):

    def setUp(self):
        self.user1 = ProfileFactory()
        self.token = TokenForgotPassword.objects.create(user=self.user1.user,
                                                        token="abcde",
                                                        date_end=datetime.now())

    def test_get_absolute_url(self):
        self.assertEqual(self.token.get_absolute_url(), '/new_password/?token={0}'.format(self.token.token))


class TestTokenRegister(TestCase):

    def setUp(self):
        self.user1 = ProfileFactory()
        self.token = TokenRegister.objects.create(user=self.user1.user,
                                                  token="abcde",
                                                  date_end=datetime.now())

    def test_get_absolute_url(self):
        self.assertEqual(self.token.get_absolute_url(), '/activation/?token={0}'.format(self.token.token))

    def test_unicode(self):
        self.assertEqual(self.token.__unicode__(), '{0} - {1}'.format(self.user1.user.username, self.token.date_end))
