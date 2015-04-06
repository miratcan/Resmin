from django import forms
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User

from apps.question.signals import user_created_question
from apps.question.models import Question


class CreateQuestionForm(forms.ModelForm):

    text = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'autocomplete': 'off'}))

    is_anonymouse = forms.BooleanField(label=_('Hide my name'), required=False)

    def save(self, *args, **kwargs):
        question = super(CreateQuestionForm, self).save(commit=False)
        question.owner = kwargs.pop('owner')
        question.save()
        user_created_question.send(sender=question)
        return question

    class Meta:
        model = Question
        fields = ['text', 'is_anonymouse']


class RequestAnswerForm(forms.Form):
    """
    TODO: User CommaSeparatedUserField at PM app instead of CharField.
    """
    questionees = forms.CharField(
        label=_('Questionees'),
        widget=forms.Textarea,
        help_text=_('Separate the usernames with comma which you request '
                    'answer. You can only request answer from your followers'))

    is_anonymouse = forms.BooleanField(label=_('Is Anonymouse'),
                                       required=False)

    def __init__(self, *args, **kwargs):
        self.questioner = kwargs.pop('questioner')
        self.qmeta = kwargs.pop('qmeta')
        super(RequestAnswerForm, self).__init__(*args, **kwargs)

    def clean_questionees(self):
        usernames = [d.strip() for d in
                     self.cleaned_data['questionees'].split(',')]
        following_users = User.objects.filter(
            id__in=self.questioner.follower_user_ids).values('username')
        available_usernames = [u['username'] for u in following_users]
        return set(usernames).intersection(available_usernames)

    def save(self):
        usernames = self.cleaned_data['questionees']
        for questionee in User.objects.filter(username__in=usernames):
            Question.objects.create(
                meta=self.qmeta, questionee=questionee,
                questioner=self.questioner,
                is_anonymouse=self.cleaned_data['is_anonymouse'])
        return usernames


class SearchForm(forms.Form):
    q = forms.CharField()
