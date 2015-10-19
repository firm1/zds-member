# coding: utf-8

from django.conf.urls import patterns, url, include

from member.views import MemberList, MemberDetail, UpdateMember, UpdatePasswordMember, \
    UpdateUsernameEmailMember, RegisterView, SendValidationEmailView

urlpatterns = patterns('',
                       #list
                       url(r'^$', MemberList.as_view(), name='member-list'),

                       #details
                       url(r'^voir/(?P<user_name>.+)/$', MemberDetail.as_view(), name='member-detail'),

                       #modification
                       url(r'^parametres/profil/$', UpdateMember.as_view(), name='update-member'),
                       url(r'^parametres/compte/$', UpdatePasswordMember.as_view(), name='update-password-member'),
                       url(r'^parametres/user/$', UpdateUsernameEmailMember.as_view(), name='update-username-email-member'),

                       #moderation
                       url(r'^profil/karmatiser/$', 'member.views.modify_karma'),
                       url(r'^profil/modifier/(?P<user_pk>\d+)/$', 'member.views.modify_profile'),
                       url(r'^parametres/mini_profil/(?P<user_name>.+)/$', 'member.views.settings_mini_profile'),
                       url(r'^profil/multi/(?P<ip_address>.+)/$', 'member.views.member_from_ip'),

                       #user rights
                       url(r'^profil/promouvoir/(?P<user_pk>\d+)/$', 'member.views.settings_promote'),

                       #membership
                       url(r'^connexion/$', 'member.views.login_view'),
                       url(r'^deconnexion/$', 'member.views.logout_view'),
                       url(r'^inscription/$', RegisterView.as_view(), name='register-member'),
                       url(r'^reinitialisation/$', 'member.views.forgot_password'),
                       url(r'^validation/$', SendValidationEmailView.as_view(), name='send-validation-email'),
                       url(r'^new_password/$', 'member.views.new_password'),
                       url(r'^activation/$', 'member.views.active_account'),
                       url(r'^envoi_jeton/$', 'member.views.generate_token_account'),
                       url(r'^desinscrire/valider/$', 'member.views.unregister'),
                       url(r'^desinscrire/avertissement/$', 'member.views.warning_unregister')
                       )

# API
urlpatterns += patterns('',
                        url(r'^api-doc/', include('rest_framework_swagger.urls')),
                        url(r'^oauth2/', include('oauth2_provider.urls', namespace='oauth2_provider')),
                        url(r'^api/', include('member.api.urls')),
                        )