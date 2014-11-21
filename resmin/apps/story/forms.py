import re

from django import forms
from django.utils.translation import ugettext as _
from django.db import transaction

from apps.notification.utils import notify
from apps.question.signals import user_created_story
from apps.story.models import Story, Slot

__author__ = 'Mirat'


class StoryForm(forms.ModelForm):

    SLOT_KEY_PATTERN = re.compile('image_(?P<image_id>\d+)_order')

    def __init__(self, *args, **kwargs):
        self.owner = kwargs.pop('owner')
        self.meta = kwargs.pop('meta', None)
        self.question = kwargs.pop('question', None)
        self.slots = self.parse_slots(kwargs.pop('slot_data', None))

        super(StoryForm, self).__init__(*args, **kwargs)
        if self.question:
            del self.fields['is_anonymouse']

    def parse_slots(self, data):
        if not data:
            return None
        slot_data = {}
        for key, val in data.iteritems():
            match = self.SLOT_KEY_PATTERN.match(key)
            if match:
                slot_data[int(match.group('image_id'))] = int(val)
        return slot_data

    @transaction.commit_on_success
    def save(self, *args, **kwargs):
        story = super(StoryForm, self).save(commit=False)
        story.owner = self.owner
        story.meta = self.question
        story.save()
        self.save_m2m()

        for image, order in self.slots.iteritems():
            Slot.objects.create(story=story, image_id=image, order=order)

        if self.question:
            self.question.status = 1
            self.question.answer = story
            self.question.save()
            notify(self.question.questionee,
                   'got_answer_to_question', self.question,
                   self.question.questioner, story.get_absolute_url())
        user_created_story.send(sender=story)
        return story

    def clean(self):
        if not self.slots:
            raise forms.ValidationError("A story must have at least one image")

        if not self.owner.is_authenticated():
            raise forms.ValidationError("You have to login to answer "
                                        "a question.")
        return self.cleaned_data

    class Meta:
        model = Story
        fields = ['title', 'visible_for', 'is_anonymouse', 'is_nsfw',
                  'description']
