from django import forms
from apps.question.models import QuestionMeta
from apps.moderation.models import QuestionMetaComplaint


class ComplainQuestionMetaForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.qmeta = kwargs.pop('qmeta')
        super(ComplainQuestionMetaForm, self).__init__(*args, **kwargs)

    class Meta:
        model = QuestionMetaComplaint
        fields = ['complain_type', 'description']

    def save(self, *args, **kwargs):
        complainer = kwargs.pop('complainer')
        complaint = QuestionMetaComplaint.objects.create(
            question_meta=self.qmeta,
            description=self.cleaned_data['description'],
            complain_type=self.cleaned_data['complain_type'])
        complaint.complainers.add(complainer)


class ModerateQuestionMetaForm(forms.ModelForm):
    class Meta:
        model = QuestionMeta
        fields = ['text', 'status', 'redirected_to']