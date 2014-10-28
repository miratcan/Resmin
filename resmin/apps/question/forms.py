from django import forms
from django.utils.translation import ugettext as _
from django.conf import settings

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
