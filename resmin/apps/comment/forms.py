from django import forms
from django.utils.translation import ugettext as _

from apps.notification.utils import notify
from apps.comment.models import Comment
from apps.follow.models import StoryFollow


class CommentForm(forms.Form):

    comment = forms.CharField(
        label='Comment',
        widget=forms.Textarea(
            attrs={'placeholder':  _('Comment')}))

    def __init__(self, *args, **kwargs):
        self.owner = kwargs.pop('owner')
        self.story = kwargs.pop('story')
        super(CommentForm, self).__init__(*args, **kwargs)

    def save(self):
        comment = Comment.objects.create(owner=self.owner,
                                         story=self.story,
                                         body=self.cleaned_data['comment'],
                                         status=Comment.PUBLISHED)
        self.story.update_comment_count(save=True)
        StoryFollow.objects.get_or_create(
            follower=comment.owner,
            target=comment.story, defaults={
                'reason': StoryFollow.REASON_COMMENTED})

        """
        Send notification.
        TODO: Run notify actions to celery task.
        """
        for follow in StoryFollow.objects.filter(target=comment.story)\
                                         .exclude(follower=comment.owner):
            ntype_slug = {
                StoryFollow.REASON_CREATED: 'new_comment_on_my_story',
                StoryFollow.REASON_COMMENTED: 'new_comment_on_commented_story'
            }[follow.reason]
            notify(ntype_slug, comment, comment.story, follow.follower,
                   comment.story.get_absolute_url())
        return comment


class UpdateCommentForm(forms.Form):

    comment = forms.CharField(
        label='Comment',
        widget=forms.Textarea(
            attrs={'placeholder':  _('Comment')}))

    def __init__(self, *args, **kwargs):
        self.comment = kwargs.pop('comment', None)
        self.base_fields['comment'].initial = self.comment.body
        super(UpdateCommentForm, self).__init__(*args, **kwargs)

    def comment_id(self):
        return self.comment.id

    def save(self):
        self.comment.body = self.cleaned_data['comment']
        self.comment.save()
        return self.comment
