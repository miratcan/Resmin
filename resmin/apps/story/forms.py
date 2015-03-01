import re

from django import forms
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext as _

from json_field.forms import JSONFormField as JSONField

from apps.question.models import Question
from apps.story.models import Story, Slot


def find_in_dictlist(k, v, dl):
    # Finds matching key value in list of dicts.
    return (i for i in dl if i[k] == v).next()


def rm_key_in_dictlist(k, dl):
    # Clean ids from extising_slots_as_new.
    [setattr(s, 'id', None) for s in dl]


class StoryForm(forms.ModelForm):

    slot_data = JSONField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        self.owner = kwargs.pop('owner')
        self.meta = kwargs.pop('meta', None)
        self.question = kwargs.pop('question', None)
        super(StoryForm, self).__init__(*args, **kwargs)

        for fn in ['title', 'description']:
            self.fields[fn].widget.attrs.update({
                'placeholder': self.fields[fn].label})

        if self.owner:
            self.fields['question'] = \
                forms.ModelChoiceField(
                    required=False,
                    initial=self.question,
                    widget=forms.HiddenInput,
                    queryset=Question.objects.filter(
                        questionee=self.owner))

    def save_slots(self, story, slot_data):
        slots = story.slot_set.all()
        slot_pks = [s.pk for s in slots]
        form_pks = [i['pk'] for i in slot_data if 'pk' in i]
        deleted_pks = set(slot_pks) - set(form_pks)
        story.slot_set.filter(id__in=deleted_pks).delete()
        slots = filter(lambda s: s.pk in form_pks, slots)
        for slot in slots:
            slot.order = find_in_dictlist(
                'cPk', slot.pk, slot_data)['order']
            slot.save()
        for sd in slot_data:
            if 'pk' not in sd:
                Slot.objects.create(
                    story=story, order=sd['order'], cPk=sd['cPk'],
                    cTp=ContentType.objects.get(id=sd['cTp']))

    def save(self, *args, **kwargs):

        # Save Story
        story = super(StoryForm, self).save(commit=False)
        story.owner = self.owner
        story.save()

        # If there's a meta add as mounted question meta.
        if self.meta:
            story.mounted_question_metas.add(self.meta)
            self.save_m2m()

        if self.question:
            self.question.status = Question.ANSWERED
            self.question.save()

        # Save slots of story.
        self.save_slots(story, self.cleaned_data['slot_data'])
        return story

    def clean(self):
        if not self.cleaned_data['slot_data']:
            raise forms.ValidationError("A story must have at least 1 image.")

        if not self.owner.is_authenticated():
            raise forms.ValidationError("You have to login to answer "
                                        "a question.")
        return self.cleaned_data

    class Meta:
        model = Story
        fields = ['title', 'visible_for', 'is_anonymouse', 'is_nsfw',
                  'description', 'question', 'slot_data']


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
            self.fields[title_key].widget.attrs.update({
                'placeholder': _('Title')})
            self.fields[descr_key] = forms.CharField(
                required=False, initial=slot.description,
                widget=forms.Textarea)
            self.fields[descr_key].widget.attrs.update({
                'placeholder': _('Description')})
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
