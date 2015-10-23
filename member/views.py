# coding: utf-8

from datetime import datetime, timedelta
import uuid

from member.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.core.context_processors import csrf
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Q
from django.utils.http import urlunquote
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import redirect, render, get_object_or_404
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_POST
from django.contrib.sites.models import Site

from django.views.generic import DetailView, UpdateView, CreateView, FormView
from member.forms import LoginForm, MiniProfileForm, ProfileForm, RegisterForm, \
    ChangePasswordForm, ChangeUserForm, NewPasswordForm, \
    PromoteMemberForm, KarmaForm, UsernameAndEmailForm

from member.models import Profile, TokenForgotPassword, TokenRegister, KarmaNote
from member.decorator import can_write_and_read_now
from member.commons import ProfileCreate, TemporaryReadingOnlySanction, ReadingOnlySanction, \
    DeleteReadingOnlySanction, TemporaryBanSanction, BanSanction, DeleteBanSanction, TokenGenerator
from member.utils.paginator import ZdSPagingListView
from member.utils.tokens import generate_token


class MemberList(ZdSPagingListView):
    """Displays the list of registered users."""

    context_object_name = 'members'
    paginate_by = settings.ZDS_MEMBER['members_per_page']
    # TODO When User will be no more used, you can make this request with
    # Profile.objects.all_members_ordered_by_date_joined()
    queryset = User.objects.filter(is_active=True) \
                           .order_by('-date_joined') \
                           .all().select_related("profile")
    template_name = 'member/index.html'


class MemberDetail(DetailView):
    """Displays details about a profile."""

    context_object_name = 'usr'
    model = User
    template_name = 'member/profile.html'

    def get_object(self, queryset=None):
        # Use urlunquote to accept quoted twice URLs (for instance in MPs send
        # through emarkdown parser)
        return get_object_or_404(User, username=urlunquote(self.kwargs['user_name']))

    def get_context_data(self, **kwargs):
        context = super(MemberDetail, self).get_context_data(**kwargs)
        usr = context['usr']
        profile = usr.profile
        context['profile'] = profile
        context['karmanotes'] = KarmaNote.objects.filter(user=usr).order_by('-create_at')
        context['karmaform'] = KarmaForm(profile)
        return context


class UpdateMember(UpdateView):
    """Updates a profile."""

    form_class = ProfileForm
    template_name = 'member/settings/profile.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UpdateMember, self).dispatch(*args, **kwargs)

    def get_object(self, queryset=None):
        return get_object_or_404(Profile, user=self.request.user)

    def get_form(self, form_class):
        profile = self.get_object()
        form = form_class(initial={
            'biography': profile.biography,
            'site': profile.site,
            'avatar_url': profile.avatar_url,
            'show_email': profile.show_email,
            'show_sign': profile.show_sign,
            'hover_or_click': profile.hover_or_click,
            'email_for_answer': profile.email_for_answer,
            'sign': profile.sign
        })

        return form

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            return self.form_valid(form)

        return render(request, self.template_name, {'form': form})

    def form_valid(self, form):
        profile = self.get_object()
        self.update_profile(profile, form)
        self.save_profile(profile)

        return redirect(self.get_success_url())

    def update_profile(self, profile, form):
        cleaned_data_options = form.cleaned_data.get('options')
        profile.biography = form.data['biography']
        profile.site = form.data['site']
        profile.show_email = 'show_email' in cleaned_data_options
        profile.show_sign = 'show_sign' in cleaned_data_options
        profile.hover_or_click = 'hover_or_click' in cleaned_data_options
        profile.email_for_answer = 'email_for_answer' in cleaned_data_options
        profile.avatar_url = form.data['avatar_url']
        profile.sign = form.data['sign']

    def get_success_url(self):
        return reverse('update-member')

    def save_profile(self, profile):
        try:
            profile.save()
            profile.user.save()
        except Profile.DoesNotExist:
            messages.error(self.request, self.get_error_message())
            return redirect(reverse('update-member'))
        messages.success(self.request, self.get_success_message())

    def get_success_message(self):
        return _(u'The profile has been updated.')

    def get_error_message(self):
        return _(u'An error has occurred.')


class UpdatePasswordMember(UpdateMember):
    """User's settings about his password."""

    form_class = ChangePasswordForm

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.user, request.POST)

        if form.is_valid():
            return self.form_valid(form)

        return render(request, self.template_name, {'form': form})

    def get_form(self, form_class):
        return form_class(self.request.user)

    def update_profile(self, profile, form):
        profile.user.set_password(form.data['password_new'])

    def get_success_message(self):
        return _(u'The password has been updated.')

    def get_success_url(self):
        return reverse('update-password-member')


class UpdateUsernameEmailMember(UpdateMember):
    """User's settings about his username and email."""

    form_class = ChangeUserForm

    def get_form(self, form_class):
        return form_class(self.request.POST)

    def update_profile(self, profile, form):
        if 'username' in form.data:
            profile.user.username = form.data['username']
        if 'email' in form.data:
            if form.data['email'].strip() != '':
                profile.user.email = form.data['email']

    def get_success_url(self):
        profile = self.get_object()

        return profile.get_absolute_url()


class RegisterView(CreateView, ProfileCreate, TokenGenerator):
    """Create a profile."""

    form_class = RegisterForm
    template_name = 'member/register/index.html'

    def get_object(self, queryset=None):
        return get_object_or_404(Profile, user=self.request.user)

    def get_form(self, form_class):
        return form_class()

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            return self.form_valid(form)
        return render(request, self.template_name, {'form': form})

    def form_valid(self, form):
        profile = self.create_profile(form.data)
        profile.last_ip_address = get_client_ip(self.request)
        self.save_profile(profile)
        token = self.generate_token(profile.user)
        self.send_email(token, profile.user)

        return render(self.request, self.get_success_template())

    def get_success_template(self):
        return 'member/register/success.html'


class SendValidationEmailView(FormView, TokenGenerator):
    """Send a validation email on demand. """

    form_class = UsernameAndEmailForm
    template_name = 'member/register/send_validation_email.html'

    usr = None

    def get_user(self, username, email):

        if username:
            self.usr = get_object_or_404(User, username=username)

        elif email:
            self.usr = get_object_or_404(User, email=email)

    def get_form(self, form_class):
        return form_class()

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            # Fetch the user
            if "username" in form.data:
                username = form.data["username"]
            else:
                username = None
            if "email" in form.data:
                email = form.data["email"]
            else:
                email = None

            self.get_user(username, email)

            # User should not be already active
            if not self.usr.is_active:
                return self.form_valid(form)
            else:
                if username is not None:
                    form.errors['username'] = form.error_class([self.get_error_message()])
                else:
                    form.errors['email'] = form.error_class([self.get_error_message()])

        return render(request, self.template_name, {'form': form})

    def form_valid(self, form):
        # Delete old token
        token = TokenRegister.objects.filter(user=self.usr)
        if token.count() >= 1:
            token.all().delete()

        # Generate new token and send email
        token = self.generate_token(self.usr)
        self.send_email(token, self.usr)

        return render(self.request, self.get_success_template())

    def get_success_template(self):
        return 'member/register/send_validation_email_success.html'

    def get_error_message(self):
        return _("Le compte est déjà activé.")


@login_required
def warning_unregister(request):
    """
    Displays a warning page showing what will happen when user unregisters.
    """
    return render(request, 'member/settings/unregister.html', {'user': request.user})


@login_required
@require_POST
@transaction.atomic
def unregister(request):
    """allow members to unregister"""

    current = request.user
    logout(request)
    User.objects.filter(pk=current.pk).delete()
    return redirect("/")


@require_POST
@can_write_and_read_now
@login_required
@transaction.atomic
def modify_profile(request, user_pk):
    """Modifies sanction of a user if there is a POST request."""

    profile = get_object_or_404(Profile, user__pk=user_pk)
    if profile.is_private():
        raise PermissionDenied
    if request.user.profile == profile:
        messages.error(request, _(u"You can't punish yourself!"))
        raise PermissionDenied

    if 'ls' in request.POST:
        state = ReadingOnlySanction(request.POST)
    elif 'ls-temp' in request.POST:
        state = TemporaryReadingOnlySanction(request.POST)
    elif 'ban' in request.POST:
        state = BanSanction(request.POST)
    elif 'ban-temp' in request.POST:
        state = TemporaryBanSanction(request.POST)
    elif 'un-ls' in request.POST:
        state = DeleteReadingOnlySanction(request.POST)
    else:
        # un-ban
        state = DeleteBanSanction(request.POST)

    try:
        ban = state.get_sanction(request.user, profile.user)
    except ValueError:
        raise HttpResponseBadRequest

    state.apply_sanction(profile, ban)

    if 'un-ls' in request.POST or 'un-ban' in request.POST:
        msg = state.get_message_unsanction()
    else:
        msg = state.get_message_sanction()

    msg = msg.format(ban.user,
                     ban.moderator,
                     ban.type,
                     state.get_detail(),
                     ban.text,
                     settings.APP_SITE['litteral_name'])

    state.notify_member(ban, msg)
    return redirect(profile.get_absolute_url())


# settings for public profile

@can_write_and_read_now
@login_required
def settings_mini_profile(request, user_name):
    """Minimal settings of users for staff."""

    # extra information about the current user
    profile = get_object_or_404(Profile, user__username=user_name)
    if request.method == "POST":
        form = MiniProfileForm(request.POST)
        data = {"form": form, "profile": profile}
        if form.is_valid():
            profile.biography = form.data["biography"]
            profile.site = form.data["site"]
            profile.avatar_url = form.data["avatar_url"]
            profile.sign = form.data["sign"]

            # Save the profile and redirect the user to the configuration space
            # with message indicate the state of the operation

            try:
                profile.save()
            except:
                messages.error(request, _(u"An error has occurred."))
                return redirect(reverse("member.views.settings_mini_profile"))

            messages.success(request, _(u"The profile has been updated."))
            return redirect(reverse("member-detail", args=[profile.user.username]))
        else:
            return render(request, "member/settings/profile.html", data)
    else:
        form = MiniProfileForm(initial={
            "biography": profile.biography,
            "site": profile.site,
            "avatar_url": profile.avatar_url,
            "sign": profile.sign,
        })
        data = {"form": form, "profile": profile}
        return render(request, "member/settings/profile.html", data)


def login_view(request):
    """Log in user."""

    csrf_tk = {}
    csrf_tk.update(csrf(request))
    error = False

    # Redirecting user once logged in?

    if "next" in request.GET:
        next_page = request.GET["next"]
    else:
        next_page = None
    if request.method == "POST":
        form = LoginForm(request.POST)
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(username=username, password=password)
        if user is not None:
            profile = get_object_or_404(Profile, user=user)
            if user.is_active:
                if profile.can_read_now():
                    login(request, user)
                    request.session["get_token"] = generate_token()
                    if "remember" not in request.POST:
                        request.session.set_expiry(0)
                    profile.last_ip_address = get_client_ip(request)
                    profile.save()
                    # redirect the user if needed
                    try:
                        return redirect(next_page)
                    except:
                        return redirect("/")
                else:
                    messages.error(request,
                                   _(u"You aren't allowed to connect "
                                     u"to the site, you have been banned by "
                                     u"a moderator."))
            else:
                messages.error(request,
                               _(u"You haven't activated your account, "
                                 u"you must do this before you can "
                                 u"log on the website. Look in your "
                                 u"mail : {}.").format(user.email))
        else:
            messages.error(request,
                           _(u"The information provided is not valid."))

    if next_page is not None:
        form = LoginForm()
        form.helper.form_action += "?next=" + next_page
    else:
        form = LoginForm()

    csrf_tk["error"] = error
    csrf_tk["form"] = form
    csrf_tk["next_page"] = next_page
    return render(request, "member/login.html",
                  {"form": form,
                   "csrf_tk": csrf_tk})


@login_required
@require_POST
def logout_view(request):
    """Log out user."""

    logout(request)
    request.session.clear()
    return redirect("/")


def forgot_password(request):
    """If the user forgot his password, he can have a new one."""

    if request.method == "POST":
        form = UsernameAndEmailForm(request.POST)
        if form.is_valid():

            # Get data from form
            data = form.data
            username = data["username"]
            email = data["email"]

            # Fetch the user, we need his email adress
            usr = None
            if username:
                usr = get_object_or_404(User, Q(username=username))

            if email:
                usr = get_object_or_404(User, Q(email=email))

            # Generate a valid token during one hour.
            uuid_token = str(uuid.uuid4())
            date_end = datetime.now() + timedelta(days=0, hours=1, minutes=0,
                                                  seconds=0)
            token = TokenForgotPassword(user=usr, token=uuid_token,
                                        date_end=date_end)
            token.save()

            # send email
            subject = _(u"{} - Mot de passe oublié").format(settings.APP_SITE['litteral_name'])
            from_email = "{} <{}>".format(settings.APP_SITE['litteral_name'],
                                          settings.APP_SITE['email_noreply'])
            current_site = Site.objects.get_current()
            context = {
                "username": usr.username,
                "site_name": settings.APP_SITE['litteral_name'],
                "site_url": current_site.domain,
                "url": current_site.domain + token.get_absolute_url()
            }
            message_html = render_to_string("email/member/confirm_forgot_password.html", context)
            message_txt = render_to_string("email/member/confirm_forgot_password.txt", context)

            msg = EmailMultiAlternatives(subject, message_txt, from_email, [usr.email])
            msg.attach_alternative(message_html, "text/html")
            msg.send()
            return render(request, "member/forgot_password/success.html")
        else:
            return render(request, "member/forgot_password/index.html",
                          {"form": form})
    form = UsernameAndEmailForm()
    return render(request, "member/forgot_password/index.html", {"form": form})


def new_password(request):
    """Create a new password for a user."""

    try:
        token = request.GET["token"]
    except KeyError:
        return redirect("/")
    token = get_object_or_404(TokenForgotPassword, token=token)
    if request.method == "POST":
        form = NewPasswordForm(token.user.username, request.POST)
        if form.is_valid():
            data = form.data
            password = data["password"]
            # User can't confirm his request if it is too late.

            if datetime.now() > token.date_end:
                return render(request, "member/new_password/failed.html")
            token.user.set_password(password)
            token.user.save()
            token.delete()
            return render(request, "member/new_password/success.html")
        else:
            return render(request, "member/new_password/index.html", {"form": form})
    form = NewPasswordForm(identifier=token.user.username)
    return render(request, "member/new_password/index.html", {"form": form})


def active_account(request):
    """Active token for a user."""

    try:
        token = request.GET["token"]
    except KeyError:
        return redirect("/")
    token = get_object_or_404(TokenRegister, token=token)
    usr = token.user

    # User can't confirm his request if he is already activated.

    if usr.is_active:
        return render(request, "member/register/token_already_used.html")

    # User can't confirm his request if it is too late.

    if datetime.now() > token.date_end:
        return render(request, "member/register/token_failed.html",
                      {"token": token})
    usr.is_active = True
    usr.save()

    # send register message

    """
    current_site = Site.objects.get_current()

    bot = get_object_or_404(User, username=settings.ZDS_MEMBER['bot_account'])
    msg = _(
        u'Bonjour **{username}**,'
        u'\n\n'
        u'Ton compte a été activé, et tu es donc officiellement '
        u'membre de la communauté de {site_name}.'
        u'\n\n'
        u'{site_name} est une communauté dont le but est de diffuser des '
        u'connaissances au plus grand nombre.'
        u'\n\n'
        u'Sur ce site, tu trouveras un ensemble de [tutoriels]({tutorials_url}) dans '
        u'plusieurs domaines et plus particulièrement autour de l\'informatique '
        u'et des sciences. Tu y retrouveras aussi des [articles]({articles_url}) '
        u'traitant de sujets d\'actualité ou non, qui, tout comme les tutoriels, '
        u'sont écrits par des [membres]({members_url}) de la communauté. '
        u'Pendant tes lectures et ton apprentissage, si jamais tu as des '
        u'questions à poser, tu retrouveras sur les [forums]({forums_url}) des personnes '
        u'prêtes à te filer un coup de main et ainsi t\'éviter de passer '
        u'plusieurs heures sur un problème.'
        u'\n\n'
        u'L\'ensemble du contenu disponible sur le site est et sera toujours gratuit, '
        u'car la communauté de {site_name} est attachée aux valeurs du libre '
        u'partage et désire apporter le savoir à tout le monde quels que soient ses moyens.'
        u'\n\n'
        u'En espérant que tu te plairas ici, '
        u'je te laisse maintenant faire un petit tour.'
        u'\n\n'
        u'Clem\'') \
        .format(username=usr.username,
                tutorials_url=current_site.domain + reverse("tutorial:list"),
                articles_url=current_site.domain + reverse("article:list"),
                members_url=current_site.domain + reverse("member-list"),
                forums_url=current_site.domain + reverse('cats-forums-list'),
                site_name=settings.APP_SITE['litteral_name'])

    send_mp(
        bot,
        [usr],
        _(u"Bienvenue sur {}").format(settings.APP_SITE['litteral_name']),
        _(u"Le manuel du nouveau membre"),
        msg,
        True,
        True,
        False,
    )
    """
    token.delete()
    form = LoginForm(initial={'username': usr.username})
    return render(request, "member/register/token_success.html", {"usr": usr, "form": form})


def generate_token_account(request):
    """Generate token for account."""

    try:
        token = request.GET["token"]
    except KeyError:
        return redirect("/")
    token = get_object_or_404(TokenRegister, token=token)

    # push date

    date_end = datetime.now() + timedelta(days=0, hours=1, minutes=0,
                                          seconds=0)
    token.date_end = date_end
    token.save()

    # send email
    subject = _(u"{} - Registration confirmation").format(settings.APP_SITE['litteral_name'])
    from_email = "{} <{}>".format(settings.APP_SITE['litteral_name'],
                                  settings.APP_SITE['email_noreply'])
    current_site = Site.objects.get_current()
    context = {
        "username": token.user.username,
        "site_url": current_site.domain,
        "site_name": settings.APP_SITE['litteral_name'],
        "url": current_site.domain + token.get_absolute_url()
    }
    message_html = render_to_string("email/member/confirm_registration.html", context)
    message_txt = render_to_string("email/member/confirm_registration.txt", context)

    msg = EmailMultiAlternatives(subject, message_txt, from_email, [token.user.email])
    msg.attach_alternative(message_html, "text/html")
    try:
        msg.send()
    except:
        msg = None
    return render(request, 'member/register/success.html', {})


def get_client_ip(request):
    """Retrieve the real IP address of the client."""

    if "HTTP_X_REAL_IP" in request.META:  # nginx
        return request.META.get("HTTP_X_REAL_IP")
    elif "REMOTE_ADDR" in request.META:
        # other
        return request.META.get("REMOTE_ADDR")
    else:
        # should never happend
        return "0.0.0.0"


@login_required
def settings_promote(request, user_pk):
    """ Manage the admin right of user. Only super user can access """

    if not request.user.is_superuser:
        raise PermissionDenied

    profile = get_object_or_404(Profile, user__pk=user_pk)
    user = profile.user

    if request.method == "POST":
        form = PromoteMemberForm(request.POST)
        data = dict(form.data.lists())

        groups = Group.objects.all()
        usergroups = user.groups.all()

        if 'groups' in data:
            for group in groups:
                if str(group.id) in data['groups']:
                    if group not in usergroups:
                        user.groups.add(group)
                        messages.success(request, _(u'{0} now belongs to the group {1}.')
                                         .format(user.username, group.name))
                else:
                    if group in usergroups:
                        user.groups.remove(group)
                        messages.warning(request, _(u'{0} now no longer belongs to the group {1}.')
                                         .format(user.username, group.name))
        else:
            user.groups.clear()
            messages.warning(request, _(u'{0} not now belong to any group.')
                             .format(user.username))

        if 'superuser' in data and u'on' in data['superuser']:
            if not user.is_superuser:
                user.is_superuser = True
                messages.success(request, _(u'{0} is now superuser.')
                                 .format(user.username))
        else:
            if user == request.user:
                messages.error(request, _(u"A superuser can't to retire from super-users."))
            else:
                if user.is_superuser:
                    user.is_superuser = False
                    messages.warning(request, _(u'{0} is no longer superuser.')
                                     .format(user.username))

        if 'activation' in data and u'on' in data['activation']:
            user.is_active = True
            messages.success(request, _(u'{0} is now activated.')
                             .format(user.username))
        else:
            user.is_active = False
            messages.warning(request, _(u'{0} is now deactivated.')
                             .format(user.username))

        user.save()

        usergroups = user.groups.all()
        """
        bot = get_object_or_404(User, username=settings.ZDS_MEMBER['bot_account'])
        msg = _(u'Bonjour {0},\n\n'
                u'Un administrateur vient de modifier les groupes '
                u'auxquels vous appartenez.  \n').format(user.username)
        if len(usergroups) > 0:
            msg = string_concat(msg, _(u'Voici la liste des groupes dont vous faites dorénavant partie :\n\n'))
            for group in usergroups:
                msg += u'* {0}\n'.format(group.name)
        else:
            msg = string_concat(msg, _(u'* Vous ne faites partie d\'aucun groupe'))
        msg += u'\n\n'
        if user.is_superuser:
            msg = string_concat(msg, _(u'Vous avez aussi rejoint le rang des super-utilisateurs. '
                                       u'N\'oubliez pas, un grand pouvoir entraîne de grandes responsabilités !'))

        send_mp(
            bot,
            [user],
            _(u'Modification des groupes'),
            u'',
            msg,
            True,
            True,
        )
        """

        return redirect(profile.get_absolute_url())

    form = PromoteMemberForm(initial={
        'superuser': user.is_superuser,
        'groups': user.groups.all(),
        'activation': user.is_active
    })
    return render(request, 'member/settings/promote.html', {
        "usr": user,
        "profile": profile,
        "form": form
    })


@login_required
def member_from_ip(request, ip_address):
    """ Get list of user connected from a particular ip """

    if not request.user.has_perm("member.change_profile"):
        raise PermissionDenied

    members = Profile.objects.filter(last_ip_address=ip_address).order_by('-last_visit')
    return render(request, 'member/settings/memberip.html', {
        "members": members,
        "ip": ip_address
    })


@login_required
@require_POST
def modify_karma(request):
    """ Add a Karma note to the user profile """

    if not request.user.has_perm("member.change_profile"):
        raise PermissionDenied

    try:
        profile_pk = request.POST["profile_pk"]
    except (KeyError, ValueError):
        raise Http404

    profile = get_object_or_404(Profile, pk=profile_pk)
    if profile.is_private():
        raise PermissionDenied

    note = KarmaNote()
    note.user = profile.user
    note.staff = request.user
    note.comment = request.POST["warning"]
    try:
        note.value = int(request.POST["points"])
    except (KeyError, ValueError):
        note.value = 0

    note.save()

    profile.karma += note.value
    profile.save()

    return redirect(reverse("member-detail", args=[profile.user.username]))
