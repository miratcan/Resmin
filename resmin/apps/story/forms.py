import re

from django import forms
from django.db import transaction

from apps.question.signals import user_created_story
from apps.question.models import Question
from apps.story.models import Story, Slot


class StoryForm(forms.ModelForm):

    SLOT_KEY_PATTERN = re.compile('image_(?P<image_id>\d+)_order')

    def __init__(self, *args, **kwargs):
        self.owner = kwargs.pop('owner')
        self.meta = kwargs.pop('meta', None)
        self.question = kwargs.pop('question', None)
        self.slots = self.parse_slots(kwargs.pop('slot_data', None))
        super(StoryForm, self).__init__(*args, **kwargs)
        if self.question:
            self.fields['question'] = \
                forms.ModelChoiceField(
                    required=False,
                    initial=self.question,
                    queryset=Question.objects.filter(
                        questionee=self.question.questionee))

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
        story.save()

        if self.meta:
            story.mounted_question_metas.add(self.meta)
            self.save_m2m()

        for image, order in self.slots.iteritems():
            updated = Slot.objects.filter(
                story=story, order=order).update(image=image)
            if not updated:
                Slot.objects.create(
                    story=story, order=order, image_id=image)
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
                  'description', 'question']


class UpdateCaptionsForm(forms.Form):

    TITLE_KEY_PATTERN = re.compile('slot_(?P<slot_id>\d+)_title')
    DESCR_KEY_PATTERN = re.compile('slot_(?P<slot_id>\d+)_descr')

    def __init__(self, *args, **kwargs):
        self.story = kwargs.pop('story')
        super(UpdateCaptionsForm, self).__init__(*args, **kwargs)
        self.stacks = []
        for slot in self.story.slot_set.all():
            title_key = 'slot_%s_title' % slot.pk
            descr_key = 'slot_%s_descr' % slot.pk
            self.fields[title_key] = forms.CharField(
                required=False, initial=slot.title)
            self.fields[descr_key] = forms.CharField(
                required=False, initial=slot.description,
                widget=forms.Textarea)
            self.stacks.append({
                'title': self[title_key],
                'descr': self[descr_key],
                'slot': slot})

    def parse_slots(self, data):
        if not data:
            return None
        slot_data = {}
        for key, val in data.iteritems():
            title_match = self.TITLE_KEY_PATTERN.match(key)
            descr_match = self.DESCR_KEY_PATTERN.match(key)
            if title_match:
                slot_id = int(title_match.group('slot_id'))
                if slot_id in slot_data:
                    slot_data[slot_id].update({'title': val})
                else:
                    slot_data[slot_id] = {'title': val}
            if descr_match:
                slot_id = int(descr_match.group('slot_id'))
                if slot_id in slot_data:
                    slot_data[slot_id].update({'descr': val})
                else:
                    slot_data[slot_id] = {'descr': val}
        return slot_data

    @transaction.commit_on_success
    def save(self, slot_data):
        data = self.parse_slots(slot_data)
        for slot_id, data in data.iteritems():
            self.story.slot_set.filter(id=slot_id).update(
                title=data['title'], description=data['descr'])
