from django import forms
from django.utils.translation import ugettext as _
from django.conf import settings

from apps.question.models import (Question, Answer)
from apps.question.signals import (user_created_question,
                                   user_created_answer)
from apps.notification.utils import notify


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


class AnswerQuestionForm(forms.ModelForm):
    """
    Must be initialized with owner and question:

    answer_form = AnswerQuestionForm(owner=request.user)
    """
    image = forms.ImageField(label=_('Select an image to submit an answer'))

    def __init__(self, *args, **kwargs):
        self.owner = kwargs.pop('owner')
        self.question = kwargs.pop('question')
        self.answer_request = kwargs.pop('answer_request', None)
        super(AnswerQuestionForm, self).__init__(*args, **kwargs)
        if self.answer_request:
            del self.fields['is_anonymouse']

    def save(self, *args, **kwargs):
        answer = super(AnswerQuestionForm, self).save(commit=False)
        answer.owner = self.owner
        answer.question = self.question
        answer.save()
        self.save_m2m()
        if self.answer_request:
            self.answer_request.status = 1
            self.answer_request.answer = answer
            self.answer_request.save()
            notify(self.answer_request.questionee,
                   'got_answer_to_answer_request', self.answer_request,
                   self.answer_request.questioner, answer.get_absolute_url())
        user_created_answer.send(sender=answer)
        return answer

    def clean(self):
        if not self.owner.is_authenticated():
            raise forms.ValidationError("You have to login to answer "
                                        "a question.")
        return self.cleaned_data

    class Meta:
        model = Answer
        fields = ['image',
                  'visible_for',
                  'is_anonymouse',
                  'is_nsfw', 'description', 'source_url']


class UpdateAnswerForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.requested_by = kwargs.pop('requested_by')
        super(UpdateAnswerForm, self).__init__(*args, **kwargs)

    def clean(self):
        if self.requested_by != self.instance.owner:
            raise forms.ValidationError(_("You can not update an answer "
                                          "that is not yours."))
        return self.cleaned_data

    class Meta:
        model = Answer
        fields = ['is_anonymouse',
                  'is_nsfw',
                  'visible_for', 'description', 'source_url']


class SearchQuestionForm(forms.Form):
    q = forms.CharField()


class DeleteQuestionForm(forms.Form):
    accepted = forms.BooleanField(label=_('Understood'))

    def __init__(self, *args, **kwargs):
        self.requested_by = kwargs.pop('requested_by')
        self.question = kwargs.pop('question')
        super(DeleteQuestionForm, self).__init__(*args, **kwargs)

    def clear(self):
        data = self.cleaned_data
        if self.question.owner is not self.requested_by:
            raise forms.ValidationError("You can not delete someone elses "
                                        "question.")

        if settings.ONLY_QUESTIONS_WITHOUT_ANSWERS_CAN_BE_DELETED:
            if self.question.answer_set.count():
                raise forms.ValidationError("You can not delete a question "
                                            "that have answers.")

        if data['accepted'] is False:
            raise forms.ValidationError("You have to accept that you want to "
                                        "delete this question.")
        return data

    def save(self):
        answers = self.question.answer_set.filter(status=0)

        if answers.count():
            self.question.status = 1
            self.question.save(fields=['status'])
        else:
            self.question.delete()

        return self.question
