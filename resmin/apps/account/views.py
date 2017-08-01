from django.core.mail import mail_admins
from django.utils.translation import ugettext as _
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.contrib.sites.shortcuts import get_current_site

from django.conf import settings
from datetime import datetime, timedelta
from django_redis import get_redis_connection

from .models import (Invitation, UserProfile,
                     EmailCandidate)
from .forms import (FollowForm, RegisterForm, UpdateProfileForm,
                    EmailCandidateForm, QuestionForm,
                    FollowerActionForm)
from ..question.models import (QuestionMeta, Question)
from django.http import HttpResponseBadRequest
from ..follow.models import UserFollow
from ..notification.utils import notify
from ..notification.decorators import delete_notification
from ..story.models import Story
from ..account.signals import follower_count_changed
from ..account.forms import NotificationPreferencesForm

from resmin.utils import paginated, send_email_from_template


redis = get_redis_connection('default')


@delete_notification
def profile(request, username=None, listing='public', action=None):

    user = get_object_or_404(User, username=username, is_active=True) if \
        username else request.user

    user_is_blocked_me, user_is_blocked_by_me,\
        i_am_follower_of_user, have_pending_follow_request \
        = False, False, False, False

    if request.user.is_authenticated():
        user_is_blocked_me = user.is_blocked_by(request.user)
        user_is_blocked_by_me = user.is_blocked_by(request.user)
        i_am_follower_of_user = request.user.is_following(user)
        have_pending_follow_request = \
            request.user.has_pending_follow_request(user)

    ctx = {'profile_user': user,
           'listing': listing,
           'user_is_blocked_by_me': user_is_blocked_by_me,
           'user_is_blocked_me': user_is_blocked_me,
           'have_pending_follow_request': have_pending_follow_request,
           'i_am_follower_of_user': i_am_follower_of_user}

    # If there are not blocks, fill ctx with answers
    if not (user_is_blocked_me or user_is_blocked_by_me):
        stories = Story.objects.build(
            frm=user, requested_user=request.user, listing=listing)
        ctx['stories'] = paginated(request, stories,
                                   settings.STORIES_PER_PAGE)
    if request.POST:
        question_form = QuestionForm(request.POST, questioner=request.user,
                                     questionee=user)
        if question_form.is_valid():
            question_form.save()
            messages.success(request, _('Your question sent to user.'))
            return HttpResponseRedirect(user.get_absolute_url())
    else:
        question_form = QuestionForm(questioner=request.user,
                                     questionee=user)

    if action:
        ctx['action'] = action
        follow_form = FollowForm(follower=request.user,
                                 target=user,
                                 action=action)
        if request.POST:
            follow_form = FollowForm(request.POST,
                                     follower=request.user,
                                     target=user,
                                     action=action)
            if follow_form.is_valid():
                follow_form.save()
                if action == 'follow':
                    messages.success(
                        request, _('Follow request sent to user'))
                elif action == 'unfollow':
                    messages.success(
                        request, _('You are not a follower anymore'))
                elif action == 'block':
                    messages.success(
                        request, _('You have blocked this user'))
                elif action == 'unblock':
                    messages.success(
                        request, _('You have unblocked this user'))
                return HttpResponseRedirect(user.get_absolute_url())

        ctx['follow_form'] = follow_form
    ctx['question_form'] = question_form

    return render(request, "auth/user_detail.html", ctx)


@login_required
def pending_follow_requests(request):
    pfr = UserFollow.objects.filter(
        status=UserFollow.PENDING, target=request.user)
    site = get_current_site(request) if not pfr else None
    return render(
        request,
        'auth/pending_follow_requests.html',
        {'pending_follow_requests': pfr,
         'site': site})


@login_required
def pending_follow_request_action(request):
    if request.method == 'POST':

        frpk = request.POST.get('pk')
        try:
            frpk = int(frpk)
        except ValueError:
            return JsonRsponse({'errMsg': 'Invalida data'}, status=400)

        action = request.POST['action']

        follow_request = get_object_or_404(
            UserFollow, pk=frpk, target=request.user)

        if action == 'accept':
            follow_request.status = UserFollow.FOLLOWING
            follow_request.save()
            follower_count_changed.send(sender=request.user)
            notify(ntype_slug='user_accepted_my_follow_request',
                   sub=follow_request.target,
                   obj=follow_request,
                   recipient=follow_request.follower,
                   url=follow_request.target.get_absolute_url())
            return JsonRsponse({'success': True})
        elif action == 'accept-restricted':
            follow_request.status = UserFollow.FOLLOWING_RESTRICTED
            follow_request.save()
            follower_count_changed.send(sender=request.user)
            notify(ntype_slug='user_accepted_my_follow_request',
                   sub=follow_request.target,
                   obj=follow_request,
                   recipient=follow_request.follower,
                   url=follow_request.target.get_absolute_url())
        if action == 'decline':
            follow_request.delete()
            return JsonRsponse({'success': True})
    return JsonRsponse({'success': False,
                        'message': 'Invalida data'})


@login_required
def update_profile(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    form = UpdateProfileForm(instance=profile)

    if request.POST:

        form = UpdateProfileForm(
            request.POST, request.FILES, instance=profile)

        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, _('Your profile updated'))
            return HttpResponseRedirect(
                reverse('profile',
                        kwargs={'username': request.user.username}))
    try:
        avatar_questionmeta = QuestionMeta.objects.get(
            id=settings.AVATAR_QUESTIONMETA_ID)
    except QuestionMeta.DoesNotExist:
        avatar_questionmeta = None
    return render(
        request,
        "auth/update_profile.html",
        {'form': form,
         'profile_user': request.user,
         'avatar_questionmeta': avatar_questionmeta})


def register(request):
    form = RegisterForm(initial={'key': request.GET.get("key", None)})
    if request.POST:
        form = RegisterForm(request.POST)
        if form.is_valid():

            user = form.save()
            user = authenticate(username=form.cleaned_data['username'],
                                password=form.cleaned_data['pass_1'])

            login(request, user)
            Invitation.objects.create(owner=user)
            messages.success(request, _('Registration complete, wellcome :)'))
            mail_admins('User %s registered.' % user,
                        'Seems, we\'re doing things well...')
            return HttpResponseRedirect("/")
    return render(request, 'auth/register.html', {'form': form})


@login_required
def invitations(request):
    return render(
        request,
        'auth/invitations.html',
        {'site': get_current_site(request),
         'profile_user': request.user,
         'invs': Invitation.objects.filter(
             owner=request.user).order_by("used_count")})


@login_required
def followers(request, username):
    if request.method == 'POST':
        action_form = FollowerActionForm(request.POST, username=username)
        if action_form.is_valid():
            result = action_form.save()
            if result:
                messages.warning(request, result)
    else:
        action_form = FollowerActionForm(username=username)
    user = get_object_or_404(User, username=username)
    user_follows = UserFollow.objects\
        .filter(target=user, follower__is_active=True)\
        .prefetch_related('follower__userprofile')
    return render(
        request,
        'auth/followers.html',
        {'profile_user': user,
         'action_form': action_form,
         'user_follows': paginated(request, user_follows,
                                   settings.QUESTIONS_PER_PAGE)})


@login_required
def followings(request, username):
    user = get_object_or_404(User, username=username)
    user_follows = UserFollow.objects\
        .filter(follower=user, target__is_active=True)\
        .prefetch_related('follower__userprofile')
    return render(
        request,
        'auth/followings.html',
        {'user': request.user,
         'profile_user': user,
         'user_follows': user_follows})


@login_required
def hof(request):
    return render(
        request,
        'auth/hof.html',
        {'profiles': UserProfile.objects.order_by('-like_count')[:40]})


@login_required
def notification_preferences(request):
    if request.method == 'POST':
        form = NotificationPreferencesForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
    else:
        form = NotificationPreferencesForm(user=request.user)
    return render(request, 'auth/notification_preferences.html', {
        'profile_user': request.user,
        'form': form})


@login_required
def email(request, key=None):
    EmailCandidate.objects.filter(
        created_at__lte=datetime.utcnow() - timedelta(days=6*30)).delete()

    if key:
        try:
            email = EmailCandidate.objects.get(key=key)
        except EmailCandidate.DoesNotExist:
            email = None

        if email:
            user = email.owner
            user.email = email.email
            user.save()
            messages.success(request, _('Your email confirmed :)'))
            mail_admins('User %s left his email: %s' % (
                user, user.email), 'Seems, we\'re doing things well...')
            return HttpResponseRedirect("/")
        else:
            return render(request, 'auth/email_form.html', {
                'key_wrong': True})
    else:
        if request.POST:
            form = EmailCandidateForm(request.POST)
            if form.is_valid():
                candidate = form.save(commit=False)
                candidate.owner = request.user
                candidate.save()
                send_email_from_template(
                    'confirmation',
                    [candidate.email],
                    {'domain': get_current_site(request),
                     'candidate': candidate})
                return render(request, 'auth/email_form.html', {
                    'profile_user': request.user})
            else:
                return render(request, 'auth/email_form.html', {
                    'form': form,
                    'profile_user': request.user})
        else:
            return render(request, 'auth/email_form.html', {
                'form': EmailCandidateForm,
                'profile_user': request.user})
