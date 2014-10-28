from django import forms
from django.utils.translation import ugettext as _
from apps.notification.utils import notify
from apps.question.signals import user_created_story
from apps.story.models import Story

__author__ = 'Mirat'


class UpdateStoryForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.requested_by = kwargs.pop('requested_by')
        super(UpdateStoryForm, self).__init__(*args, **kwargs)

    def clean(self):
        if self.requested_by != self.instance.owner:
            raise forms.ValidationError(_("You can not update an answer "
                                          "that is not yours."))
        return self.cleaned_data

    class Meta:
        model = Story
        """
        fields = ['is_anonymouse',
                  'is_nsfw',
                  'visible_for', 'description', 'source_url']
        """

class CreateStoryForm(forms.ModelForm):
    """
    Must be initialized with owner and question:

    answer_form = CreateStoryForm(owner=request.user)
    """

    def __init__(self, *args, **kwargs):
        self.owner = kwargs.pop('owner')
        self.meta = kwargs.pop('meta', None)
        self.question = kwargs.pop('question', None)
        super(CreateStoryForm, self).__init__(*args, **kwargs)
        if self.question:
            del self.fields['is_anonymouse']

    def save(self, *args, **kwargs):
        story = super(CreateStoryForm, self).save(commit=False)
        story.owner = self.owner
        story.question = self.question
        story.meta = self.meta
        story.save()
        self.save_m2m()

        if self.question:
            self.question.status = 1
            self.question.answer = story
            self.question.save()
            notify(self.answer_request.questionee,
                   'got_answer_to_answer_request', self.answer_request,
                   self.answer_request.questioner, answer.get_absolute_url())
        user_created_story.send(sender=story)
        return story

    def clean(self):
        if not self.owner.is_authenticated():
            raise forms.ValidationError("You have to login to answer "
                                        "a question.")
        return self.cleaned_data

    class Meta:
        model = Story
        fields = ['title', 'visible_for', 'is_anonymouse', 'is_nsfw',
                  'description']
