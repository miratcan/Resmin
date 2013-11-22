from django import forms
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from apps.account.models import Invitation, UserProfile, EmailCandidate

from apps.follow.models import UserFollow


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
        try:
            invitation = Invitation.objects.get(key=key)
        except Invitation.DoesNotExist:
            invitation = None

        if invitation:
            if invitation.used_by:
                raise forms.ValidationError(_("This key is used by someone "
                                              "else before"))
            else:
                return key
        else:
            raise forms.ValidationError(_("Invalid invitation key"))

    def save(self):
        user = User.objects.create_user(username=self.cleaned_data['username'],
                                        password=self.cleaned_data['pass_1'])
        invitation = Invitation.objects.get(key=self.cleaned_data['key'])
        invitation.used_by = user
        invitation.save()
        return user


class UpdateProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        exclude = ['user', 'like_count', 'avatar']


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
    	UserFollow.objects.filter(follower=self.follower, target=self.target).delete()
    	if self.action == 'follow':
            UserFollow.objects.create(
                follower=self.follower, target=self.target)
            return True    		
        if self.action == 'block':
            UserFollow.objects.create(
                follower=self.follower, target=self.target, status=2)
            return True
