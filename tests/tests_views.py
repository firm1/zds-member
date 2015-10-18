# coding: utf-8

import os
import shutil
from member.conf import settings
from django.contrib.auth.models import User, Group
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

from member.factories import ProfileFactory, StaffProfileFactory, NonAsciiProfileFactory, UserFactory
from member.models import Profile, KarmaNote, TokenForgotPassword
from member.models import TokenRegister, Ban


BASE_DIR = settings.BASE_DIR
ZDS_MEMBER = settings.ZDS_MEMBER


@override_settings(MEDIA_ROOT=os.path.join(BASE_DIR, 'media-test'))
class MemberTests(TestCase):

    def setUp(self):
        settings.EMAIL_BACKEND = \
            'django.core.mail.backends.locmem.EmailBackend'
        self.mas = ProfileFactory()
        ZDS_MEMBER['bot_account'] = self.mas.user.username
        self.anonymous = UserFactory(
            username=settings.ZDS_MEMBER["anonymous_account"],
            password="anything")
        self.external = UserFactory(
            username=settings.ZDS_MEMBER["external_account"],
            password="anything")
        self.staff = StaffProfileFactory().user

        self.bot = Group(name=settings.ZDS_MEMBER["bot_group"])
        self.bot.save()

    def test_list_members(self):
        """
        To test the listing of the members with and without page parameter.
        """

        # create strange member
        weird = ProfileFactory()
        weird.user.username = u"ïtrema718"
        weird.user.email = u"foo@\xfbgmail.com"
        weird.user.save()

        # list of members.
        result = self.client.get(
            reverse('member-list'),
            follow=False
        )
        self.assertEqual(result.status_code, 200)

        nb_users = len(result.context['members'])

        # Test that inactive user don't show up
        unactive_user = UserFactory()
        unactive_user.is_active = False
        unactive_user.save()
        result = self.client.get(
            reverse('member-list'),
            follow=False
        )
        self.assertEqual(result.status_code, 200)
        self.assertEqual(nb_users, len(result.context['members']))

        # list of members with page parameter.
        result = self.client.get(
            reverse('member-list') + u'?page=1',
            follow=False
        )
        self.assertEqual(result.status_code, 200)

        # page which doesn't exist.
        result = self.client.get(
            reverse('member-list') +
            u'?page=1534',
            follow=False
        )
        self.assertEqual(result.status_code, 404)

        # page parameter isn't an integer.
        result = self.client.get(
            reverse('member-list') +
            u'?page=abcd',
            follow=False
        )
        self.assertEqual(result.status_code, 404)

    def test_details_member(self):
        """
        To test details of a member given.
        """

        # details of a staff user.
        result = self.client.get(
            reverse('member-detail', args=[self.staff.username]),
            follow=False
        )
        self.assertEqual(result.status_code, 200)

        # details of an unknown user.
        result = self.client.get(
            reverse('member-detail', args=['unknown_user']),
            follow=False
        )
        self.assertEqual(result.status_code, 404)

    def test_profile_page_of_weird_member_username(self):

        # create some user with weird username
        user_1 = ProfileFactory()
        user_2 = ProfileFactory()
        user_3 = ProfileFactory()
        user_1.user.username = u"ïtrema"
        user_1.user.save()
        user_2.user.username = u"&#34;a"
        user_2.user.save()
        user_3.user.username = u"_`_`_`_"
        user_3.user.save()

        # profile pages of weird users.
        result = self.client.get(
            reverse('member-detail', args=[user_1.user.username]),
            follow=True
        )
        self.assertEqual(result.status_code, 200)
        result = self.client.get(
            reverse('member-detail', args=[user_2.user.username]),
            follow=True
        )
        self.assertEqual(result.status_code, 200)
        result = self.client.get(
            reverse('member-detail', args=[user_3.user.username]),
            follow=True
        )
        self.assertEqual(result.status_code, 200)

    def test_modify_member(self):

        # we need staff right for update other profile
        self.client.logout()
        self.client.login(username=self.staff.username, password="hostel77")

        # an inexistant member return 404
        result = self.client.get(
            reverse('member.views.settings_mini_profile', args=["xkcd"]),
            follow=False
        )
        self.assertEqual(result.status_code, 404)

        # an existant member return 200
        result = self.client.get(
            reverse('member.views.settings_mini_profile', args=[self.mas.user.username]),
            follow=False
        )
        self.assertEqual(result.status_code, 200)

    def test_login(self):
        """
        To test user login.
        """
        user = ProfileFactory()

        # login a user. Good password then redirection to the homepage.
        result = self.client.post(
            reverse('member.views.login_view'),
            {'username': user.user.username,
             'password': 'hostel77',
             'remember': 'remember'},
            follow=False)

        # login failed with bad password then no redirection
        # (status_code equals 200 and not 302).
        result = self.client.post(
            reverse('member.views.login_view'),
            {'username': user.user.username,
             'password': 'hostel',
             'remember': 'remember'},
            follow=False)
        self.assertEqual(result.status_code, 200)

        # login a user. Good password and next parameter then
        # redirection to the "next" page.
        result = self.client.post(
            reverse('member.views.login_view') +
            '?next=/',
            {'username': user.user.username,
             'password': 'hostel77',
             'remember': 'remember'},
            follow=False)
        self.assertRedirects(result, "/")

        # check if the login form will redirect if there is
        # a next parameter.
        self.client.logout()
        result = self.client.get(
            reverse('member.views.login_view') +
            '?next=/')
        self.assertContains(result,
                            reverse('member.views.login_view') + '?next=/')

    def test_register(self):
        """
        To test user registration.
        """

        # register a new user.
        result = self.client.post(
            reverse('register-member'),
            {
                'username': 'firm1',
                'password': 'flavour',
                'password_confirm': 'flavour',
                'email': 'firm1@zestedesavoir.com'},
            follow=False)
        self.assertEqual(result.status_code, 200)

        # check email has been sent.
        # self.assertEquals(len(mail.outbox), 1)

        # check if the new user is well inactive.
        user = User.objects.get(username='firm1')
        self.assertFalse(user.is_active)

        # make a request on the link which has been sent in mail to
        # confirm the registration.
        token = TokenRegister.objects.get(user=user)
        result = self.client.get(
            token.get_absolute_url(),
            follow=False)
        self.assertEqual(result.status_code, 200)

        # check a new email has been sent at the new user.
        # self.assertEquals(len(mail.outbox), 2)

        # check if the new user is active.
        self.assertTrue(User.objects.get(username='firm1').is_active)

    def test_unregister(self):
        """
        To test that unregistering user is working.
        """

        # test not logged user can't unregister.
        self.client.logout()
        result = self.client.post(
            reverse('member.views.unregister'),
            follow=False)
        self.assertEqual(result.status_code, 302)

        # test logged user can register.
        user = ProfileFactory()
        login_check = self.client.login(
            username=user.user.username,
            password='hostel77')
        self.assertEqual(login_check, True)
        result = self.client.post(
            reverse('member.views.unregister'),
            follow=False)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(User.objects.filter(username=user.user.username).count(), 0)

        # Attach a user at tutorials, articles, topics and private topics. After that,
        # unregister this user and check that he is well removed in all contents.
        user = ProfileFactory()

        # login and unregister:
        login_check = self.client.login(
            username=user.user.username,
            password='hostel77')
        self.assertEqual(login_check, True)
        result = self.client.post(
            reverse('member.views.unregister'),
            follow=False)
        self.assertEqual(result.status_code, 302)

    def test_forgot_password(self):
        """To test nominal scenario of a lost password."""

        # Empty the test outbox
        mail.outbox = []

        result = self.client.post(
            reverse('member.views.forgot_password'),
            {
                'username': self.mas.user.username,
                'email': '',
            },
            follow=False)

        self.assertEqual(result.status_code, 200)

        # check email has been sent
        self.assertEquals(len(mail.outbox), 1)

        # clic on the link which has been sent in mail
        user = User.objects.get(username=self.mas.user.username)

        token = TokenForgotPassword.objects.get(user=user)
        result = self.client.get(
            token.get_absolute_url(),
            follow=False)

        self.assertEqual(result.status_code, 200, "bad response code for : {}".format(token.get_absolute_url()))

    def test_sanctions(self):
        """
        Test various sanctions.
        """

        staff = StaffProfileFactory()
        login_check = self.client.login(
            username=staff.user.username,
            password='hostel77')
        self.assertEqual(login_check, True)

        # Test: LS
        user_ls = ProfileFactory()
        result = self.client.post(
            reverse(
                'member.views.modify_profile', kwargs={
                    'user_pk': user_ls.user.id}), {
                'ls': '', 'ls-text': 'Texte de test pour LS'}, follow=False)
        user = Profile.objects.get(id=user_ls.id)    # Refresh profile from DB
        self.assertEqual(result.status_code, 302)
        self.assertFalse(user.can_write)
        self.assertTrue(user.can_read)
        self.assertIsNone(user.end_ban_write)
        self.assertIsNone(user.end_ban_read)
        ban = Ban.objects.filter(user__id=user.user.id).order_by('-pubdate')[0]
        self.assertEqual(ban.type, 'Lecture Seule')
        self.assertEqual(ban.text, 'Texte de test pour LS')
        # self.assertEquals(len(mail.outbox), 1)

        # Test: Un-LS
        result = self.client.post(
            reverse(
                'member.views.modify_profile', kwargs={
                    'user_pk': user_ls.user.id}), {
                'un-ls': '', 'unls-text': 'Texte de test pour un-LS'},
            follow=False)
        user = Profile.objects.get(id=user_ls.id)    # Refresh profile from DB
        self.assertEqual(result.status_code, 302)
        self.assertTrue(user.can_write)
        self.assertTrue(user.can_read)
        self.assertIsNone(user.end_ban_write)
        self.assertIsNone(user.end_ban_read)
        ban = Ban.objects.filter(user__id=user.user.id).order_by('-id')[0]
        self.assertEqual(ban.type, u'Autorisation d\'écrire')
        self.assertEqual(ban.text, 'Texte de test pour un-LS')
        # self.assertEquals(len(mail.outbox), 2)

        # Test: LS temp
        user_ls_temp = ProfileFactory()
        result = self.client.post(
            reverse(
                'member.views.modify_profile', kwargs={
                    'user_pk': user_ls_temp.user.id}), {
                'ls-temp': '', 'ls-jrs': 10,
                'ls-text': u'Texte de test pour LS TEMP'},
            follow=False)
        user = Profile.objects.get(id=user_ls_temp.id)   # Refresh profile from DB
        self.assertEqual(result.status_code, 302)
        self.assertFalse(user.can_write)
        self.assertTrue(user.can_read)
        self.assertIsNotNone(user.end_ban_write)
        self.assertIsNone(user.end_ban_read)
        ban = Ban.objects.filter(user__id=user.user.id).order_by('-id')[0]
        self.assertEqual(ban.type, u'Lecture Seule Temporaire')
        self.assertEqual(ban.text, u'Texte de test pour LS TEMP')
        # self.assertEquals(len(mail.outbox), 3)

        # Test: BAN
        user_ban = ProfileFactory()
        result = self.client.post(
            reverse(
                'member.views.modify_profile', kwargs={
                    'user_pk': user_ban.user.id}), {
                'ban': '', 'ban-text': u'Texte de test pour BAN'}, follow=False)
        user = Profile.objects.get(id=user_ban.id)    # Refresh profile from DB
        self.assertEqual(result.status_code, 302)
        self.assertTrue(user.can_write)
        self.assertFalse(user.can_read)
        self.assertIsNone(user.end_ban_write)
        self.assertIsNone(user.end_ban_read)
        ban = Ban.objects.filter(user__id=user.user.id).order_by('-id')[0]
        self.assertEqual(ban.type, u'Ban définitif')
        self.assertEqual(ban.text, u'Texte de test pour BAN')
        # self.assertEquals(len(mail.outbox), 4)

        # Test: un-BAN
        result = self.client.post(
            reverse(
                'member.views.modify_profile', kwargs={
                    'user_pk': user_ban.user.id}),
            {'un-ban': '',
             'unban-text': u'Texte de test pour BAN'},
            follow=False)
        user = Profile.objects.get(id=user_ban.id)    # Refresh profile from DB
        self.assertEqual(result.status_code, 302)
        self.assertTrue(user.can_write)
        self.assertTrue(user.can_read)
        self.assertIsNone(user.end_ban_write)
        self.assertIsNone(user.end_ban_read)
        ban = Ban.objects.filter(user__id=user.user.id).order_by('-id')[0]
        self.assertEqual(ban.type, u'Autorisation de se connecter')
        self.assertEqual(ban.text, u'Texte de test pour BAN')
        # self.assertEquals(len(mail.outbox), 5)

        # Test: BAN temp
        user_ban_temp = ProfileFactory()
        result = self.client.post(
            reverse('member.views.modify_profile',
                    kwargs={'user_pk': user_ban_temp.user.id}),
            {'ban-temp': '', 'ban-jrs': 10,
             'ban-text': u'Texte de test pour BAN TEMP'},
            follow=False)
        user = Profile.objects.get(
            id=user_ban_temp.id)    # Refresh profile from DB
        self.assertEqual(result.status_code, 302)
        self.assertTrue(user.can_write)
        self.assertFalse(user.can_read)
        self.assertIsNone(user.end_ban_write)
        self.assertIsNotNone(user.end_ban_read)
        ban = Ban.objects.filter(user__id=user.user.id).order_by('-id')[0]
        self.assertEqual(ban.type, u'Ban Temporaire')
        self.assertEqual(ban.text, u'Texte de test pour BAN TEMP')
        # self.assertEquals(len(mail.outbox), 6)

    def test_failed_bot_sanctions(self):

        staff = StaffProfileFactory()
        login_check = self.client.login(
            username=staff.user.username,
            password='hostel77')
        self.assertEqual(login_check, True)

        bot_profile = ProfileFactory()
        bot_profile.user.groups.add(self.bot)
        bot_profile.user.save()

        # Test: LS
        result = self.client.post(
            reverse(
                'member.views.modify_profile', kwargs={
                    'user_pk': bot_profile.user.id}), {
                'ls': '', 'ls-text': 'Texte de test pour LS'}, follow=False)
        user = Profile.objects.get(id=bot_profile.id)    # Refresh profile from DB
        self.assertEqual(result.status_code, 403)
        self.assertTrue(user.can_write)
        self.assertTrue(user.can_read)
        self.assertIsNone(user.end_ban_write)
        self.assertIsNone(user.end_ban_read)

    def test_nonascii(self):
        user = NonAsciiProfileFactory()
        result = self.client.get(reverse('member.views.login_view') + '?next=' +
                                 reverse('member-detail', args=[user.user.username]),
                                 follow=False)
        self.assertEqual(result.status_code, 200)

    def test_promote_interface(self):
        """
        Test promotion interface.
        """

        # create users (one regular, one staff and one superuser)
        tester = ProfileFactory()
        staff = StaffProfileFactory()
        tester.user.is_active = False
        tester.user.save()
        staff.user.is_superuser = True
        staff.user.save()

        # create groups
        group = Group.objects.create(name="DummyGroup_1")
        groupbis = Group.objects.create(name="DummyGroup_2")

        # LET THE TEST BEGIN !

        # tester shouldn't be able to connect
        login_check = self.client.login(
            username=tester.user.username,
            password='hostel77')
        self.assertEqual(login_check, False)

        # connect as staff (superuser)
        login_check = self.client.login(
            username=staff.user.username,
            password='hostel77')
        self.assertEqual(login_check, True)

        # check that we can go through the page
        result = self.client.get(
            reverse('member.views.settings_promote',
                    kwargs={'user_pk': tester.user.id}), follow=False)
        self.assertEqual(result.status_code, 200)

        # give user rights and groups thanks to staff (but account still not activated)
        result = self.client.post(
            reverse('member.views.settings_promote',
                    kwargs={'user_pk': tester.user.id}),
            {
                'groups': [group.id, groupbis.id],
                'superuser': "on",
            }, follow=False)
        self.assertEqual(result.status_code, 302)
        tester = Profile.objects.get(id=tester.id)  # refresh

        self.assertEqual(len(tester.user.groups.all()), 2)
        self.assertFalse(tester.user.is_active)
        self.assertTrue(tester.user.is_superuser)

        # retract all right, keep one group only and activate account
        result = self.client.post(
            reverse('member.views.settings_promote',
                    kwargs={'user_pk': tester.user.id}),
            {
                'groups': [group.id],
                'activation': "on"
            }, follow=False)
        self.assertEqual(result.status_code, 302)
        tester = Profile.objects.get(id=tester.id)  # refresh

        self.assertEqual(len(tester.user.groups.all()), 1)
        self.assertTrue(tester.user.is_active)
        self.assertFalse(tester.user.is_superuser)

        # no groups specified
        result = self.client.post(
            reverse('member.views.settings_promote',
                    kwargs={'user_pk': tester.user.id}),
            {
                'activation': "on"
            }, follow=False)
        self.assertEqual(result.status_code, 302)
        tester = Profile.objects.get(id=tester.id)  # refresh

        # check that staff can't take away it's own super user rights
        result = self.client.post(
            reverse('member.views.settings_promote',
                    kwargs={'user_pk': staff.user.id}),
            {
                'activation': "on"
            }, follow=False)
        self.assertEqual(result.status_code, 302)
        staff = Profile.objects.get(id=staff.id)  # refresh
        self.assertTrue(staff.user.is_superuser)  # still superuser !

        # Finally, check that user can connect and can not access the interface
        login_check = self.client.login(
            username=tester.user.username,
            password='hostel77')
        self.assertEqual(login_check, True)
        result = self.client.post(
            reverse('member.views.settings_promote',
                    kwargs={'user_pk': staff.user.id}),
            {
                'activation': "on"
            }, follow=False)
        self.assertEqual(result.status_code, 403)  # forbidden !

    def test_filter_member_ip(self):
        """
        Test filter member by ip.
        """

        # create users (one regular and one staff and superuser)
        tester = ProfileFactory()
        staff = StaffProfileFactory()

        # test login normal user
        result = self.client.post(
            reverse('member.views.login_view'),
            {'username': tester.user.username,
             'password': 'hostel77',
             'remember': 'remember'},
            follow=False)
        # good password then redirection
        self.assertEqual(result.status_code, 302)

        # Check that the filter can't be access from normal user
        result = self.client.post(
            reverse('member.views.member_from_ip',
                    kwargs={'ip_address': tester.last_ip_address}),
            {}, follow=False)
        self.assertEqual(result.status_code, 403)

        # log the staff user
        result = self.client.post(
            reverse('member.views.login_view'),
            {'username': staff.user.username,
             'password': 'hostel77',
             'remember': 'remember'},
            follow=False)
        # good password then redirection
        self.assertEqual(result.status_code, 302)

        # test that we retrieve correctly the 2 members (staff + user) from this ip
        result = self.client.post(
            reverse('member.views.member_from_ip',
                    kwargs={'ip_address': staff.last_ip_address}),
            {}, follow=False)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(result.context['members']), 2)

    def test_modify_user_karma(self):
        """
        To test karma of a user modified by a staff user.
        """
        tester = ProfileFactory()
        staff = StaffProfileFactory()

        # login as user
        result = self.client.post(
            reverse('member.views.login_view'),
            {'username': tester.user.username,
             'password': 'hostel77'},
            follow=False)
        self.assertEqual(result.status_code, 302)

        # check that user can't use this feature
        result = self.client.post(reverse('member.views.modify_karma'), follow=False)
        self.assertEqual(result.status_code, 403)

        # login as staff
        result = self.client.post(
            reverse('member.views.login_view'),
            {'username': staff.user.username,
             'password': 'hostel77'},
            follow=False)
        self.assertEqual(result.status_code, 302)

        # try to give a few bad points to the tester
        result = self.client.post(
            reverse('member.views.modify_karma'),
            {'profile_pk': tester.pk,
             'warning': 'Bad tester is bad !',
             'points': '-50'},
            follow=False)
        self.assertEqual(result.status_code, 302)
        tester = Profile.objects.get(pk=tester.pk)
        self.assertEqual(tester.karma, -50)
        self.assertEqual(KarmaNote.objects.filter(user=tester.user).count(), 1)

        # Now give a few good points
        result = self.client.post(
            reverse('member.views.modify_karma'),
            {'profile_pk': tester.pk,
             'warning': 'Good tester is good !',
             'points': '10'},
            follow=False)
        self.assertEqual(result.status_code, 302)
        tester = Profile.objects.get(pk=tester.pk)
        self.assertEqual(tester.karma, -40)
        self.assertEqual(KarmaNote.objects.filter(user=tester.user).count(), 2)

        # Now access some unknow user
        result = self.client.post(
            reverse('member.views.modify_karma'),
            {'profile_pk': 9999,
             'warning': 'Good tester is good !',
             'points': '10'},
            follow=False)
        self.assertEqual(result.status_code, 404)

        # Now give unknow point
        result = self.client.post(
            reverse('member.views.modify_karma'),
            {'profile_pk': tester.pk,
             'warning': 'Good tester is good !',
             'points': ''},
            follow=False)
        self.assertEqual(result.status_code, 302)
        tester = Profile.objects.get(pk=tester.pk)
        self.assertEqual(tester.karma, -40)
        self.assertEqual(KarmaNote.objects.filter(user=tester.user).count(), 3)

        # Now give no point at all
        result = self.client.post(
            reverse('member.views.modify_karma'),
            {'profile_pk': tester.pk,
             'warning': 'Good tester is good !'},
            follow=False)
        self.assertEqual(result.status_code, 302)
        tester = Profile.objects.get(pk=tester.pk)
        self.assertEqual(tester.karma, -40)
        self.assertEqual(KarmaNote.objects.filter(user=tester.user).count(), 4)

        # Now access without post
        result = self.client.get(reverse('member.views.modify_karma'), follow=False)
        self.assertEqual(result.status_code, 405)

    def tearDown(self):
        if os.path.isdir(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)
