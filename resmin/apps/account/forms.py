import re

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from apps.account.models import (Invitation, UserProfile, EmailCandidate)

from apps.follow.models import UserFollow
from apps.notification.models import (NotificationType, NotificationPreference,
                                      notification_preferences)
from apps.question.models import Question, QuestionMeta
from apps.account.signals import (follower_count_changed,
                                  following_count_changed)

from libs import key_generator


class RegisterForm(forms.Form):
    username = forms.SlugField(label=_('Username'))
    pass_1 = forms.CharField(label=_('Password'), widget=forms.PasswordInput)
    pass_2 = forms.CharField(label=_('Password Again'),
                             widget=forms.PasswordInput)
    key = forms.CharField(label=_('Invitation Key'))

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).count():
            raise forms.ValidationError(_("User with this username already "
                                          "exists"))
        return username

    def clean_pass_2(self):
        pass_1 = self.cleaned_data['pass_1']
        pass_2 = self.cleaned_data['pass_2']

        if pass_1 != pass_2:
            raise forms.ValidationError(_("Password fields must be same"))
        return pass_2

    def clean_key(self):
        key = self.cleaned_data['key']

        # If there is key_prefix, we don't need to check key is exists.
        # It will be created on fly
        if key in settings.FIXED_INVITATION_KEYS:
            return key

        # Check invitation key exists and is not used.
        try:
            invitation = Invitation.objects.get(key=key)
        except Invitation.DoesNotExist:
            invitation = None

        if invitation:
            if not invitation.is_usable:
                raise forms.ValidationError(_("This key reached it's maximum "
                                              "use limit. It cant be used "
                                              "anymore."))
            else:
                return key
        else:
            raise forms.ValidationError(_("Invalid invitation key"))

    def save(self):
        user = User.objects.create_user(username=self.cleaned_data['username'],
                                        password=self.cleaned_data['pass_1'])

        key = self.cleaned_data['key']

        # If key in FIXED_INVITATION_KEYS, create an invitation
        if key in settings.FIXED_INVITATION_KEYS:
            invitation = Invitation(
                key=key_generator(prefix=key))

        # Else use existing one.
        else:
            invitation = Invitation.objects.get(key=key)
        invitation.registered_users.add(user)
        invitation.save()
        return user


class UpdateProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'website', 'location']


class EmailCandidateForm(forms.ModelForm):
    class Meta:
        model = EmailCandidate
        fields = ['email']


class DeleteQuestionForm(forms.Form):
    accepted = forms.BooleanField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        self.requested_by = kwargs.pop('requested_by')
        self.question = kwargs.pop('question')
        super(DeleteQuestionForm, self).__init__(*args, **kwargs)

    def clean_accepted(self):
        accepted = self.cleaned_data.get('accepted')

        if not accepted:
            raise forms.ValidationError("You have to accept that you want to "
                                        "delete this question.")
        return accepted

    def clean(self):
        data = self.cleaned_data
        if self.question.owner is not self.requested_by:
            raise forms.ValidationError("You can not delete someone elses "
                                        "question.")

        if settings.ONLY_QUESTIONS_WITHOUT_ANSWERS_CAN_BE_DELETED:
            if self.question.answer_set.count():
                raise forms.ValidationError("You can not delete a question "
                                            "that have answers.")
        return data

    def save(self):
        answers = self.question.answer_set.filter(status=0)

        if answers.count():
            self.question.status = 1
            self.question.save()
        else:
            self.question.delete()

        return self.question


class NotificationPreferencesForm(forms.Form):

    FIELD_LABEL_MAP = {
        'send_email_notification': _('send email notification'),
        'send_site_notification': _('send site notification')
    }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(NotificationPreferencesForm, self).__init__(*args, **kwargs)
        self.stacks = []
        for ntype in NotificationType.objects.filter(is_active=True):
            fields = []
            user_preferences = notification_preferences(
                self.user.id, ntype.slug)
            for slug, name in self.FIELD_LABEL_MAP.iteritems():
                key = '%s_when_%s' % (slug, ntype.slug)
                self.fields[key] = forms.BooleanField(
                    label=name,
                    initial=user_preferences.get(slug, False),
                    required=False)
                fields.append(self[key])
            self.stacks.append({
                'name': ntype.name,
                'fields': fields})

    def parse_preferences(self):
        events = {}
        for key, data in self.cleaned_data.iteritems():
            action_slug, event_slug = key.split('_when_')
            if event_slug in events:
                events[event_slug].update({action_slug: data})
            else:
                events[event_slug] = {action_slug: data}
        return events

    def save(self):
        """
        TODO: Optimise to not save unchanged preferences.
        """
        form_preferences = self.parse_preferences()
        for ntype in NotificationType.objects.filter(is_active=True):
            user_preferences = notification_preferences(self.user, ntype.slug)
            user_preferences.update(form_preferences.get(ntype.slug, {}))
            NotificationPreference.objects.filter(
                user=self.user, ntype=ntype).update(
                    preferences=user_preferences)


class FollowForm(forms.Form):
    """
    Blocks or unblocks user
    """

    def __init__(self, *args, **kwargs):
        self.follower = kwargs.pop('follower')
        self.target = kwargs.pop('target')
        self.action = kwargs.pop('action')
        super(FollowForm, self).__init__(*args, **kwargs)

    def clean(self):
        if self.follower == self.target:
            raise forms.ValidationError(
                _('You can not do that action on yourself.'))
        return self.cleaned_data

    def save(self):

        UserFollow.objects.filter(
            follower=self.follower, target=self.target).delete()

        if self.action == 'follow':
            UserFollow.objects.create(
                follower=self.follower, target=self.target)

        if self.action == 'block':
            UserFollow.objects.create(
                follower=self.follower, target=self.target, status=2)
        if self.action in ('unfollow', 'block', 'unblock'):
            follower_count_changed.send(sender=self.target)
            following_count_changed.send(sender=self.follower)


class FollowerActionForm(forms.Form):

    action = forms.ChoiceField(choices=(
        ('make-follow', 'Make Follow'),
        ('make-unfollow', 'Make Unfollow'),
        ('make-restricted', 'Make Restricted')), widget=forms.TextInput)

    follow = forms.ModelChoiceField(
        queryset=UserFollow.objects.none(),
        widget=forms.TextInput)

    def _make_unfollow(request, follow):
        follow.delete()
        return _('You made %s unfollow you.') % \
            follow.follower.username

    def _make_follow(request, follow):
        if follow.status == UserFollow.FOLLOWING_RESTRICTED:
            follow.status = UserFollow.FOLLOWING
            follow.save()
            return _('You set %s as follower.') % follow.follower.username

    def _make_restricted(request, follow):
        if follow.status == UserFollow.FOLLOWING:
            follow.status = UserFollow.FOLLOWING_RESTRICTED
            follow.save()
            return _('You set %s as restricted follower.') % \
                follow.follower.username

    def __init__(self, *args, **kwargs):
        self.username = kwargs.pop('username')
        self.base_fields['follow'].queryset = UserFollow.objects.filter(
            target__username=self.username)
        super(FollowerActionForm, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        action_key = self.cleaned_data['action']
        follow = self.cleaned_data['follow']
        if action_key:
            method = {u'make-follow': self._make_follow,
                      u'make-restricted': self._make_restricted,
                      u'make-unfollow': self._make_unfollow}.get(action_key)
            if method:
                return method(follow)


class QuestionForm(forms.Form):
    question = forms.CharField(label=_('Ask me a question:'), max_length=512)
    is_anonymouse = forms.BooleanField(label=_('Ask as anonymouse'),
                                       required=False, initial=True)

    def __init__(self, *args, **kwargs):
        self.questioner = kwargs.pop('questioner')
        self.questionee = kwargs.pop('questionee')
        super(QuestionForm, self).__init__(*args, **kwargs)

    def clean(self):
        if not self.questioner.is_authenticated():
            raise forms.ValidationError('You have to login to ask a question.')

    def save(self):
        meta = QuestionMeta.objects.get_or_create(
            text=self.cleaned_data['question'],
            defaults={'owner': self.questioner})[0]
        question = Question.objects.create(
            meta=meta,
            questioner=self.questioner,
            questionee=self.questionee,
            is_anonymouse=self.cleaned_data['is_anonymouse'])
        return question

    class Meta:
        model = QuestionMeta
        fields = ['question', 'is_anonymouse']
