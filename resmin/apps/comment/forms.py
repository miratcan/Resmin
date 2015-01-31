from django import forms

from apps.notification.utils import notify
from apps.comment.models import Comment
from apps.follow.models import StoryFollow


class CommentForm(forms.Form):
    comment = forms.CharField(
        label='Comment',
        widget=forms.Textarea(
            attrs={'placeholder': 'Comment'}))

    def __init__(self, *args, **kwargs):
        self.owner = kwargs.pop('owner')
        self.story = kwargs.pop('story')
        self.comment_id = kwargs.pop('comment_id', None)
        super(CommentForm, self).__init__(*args, **kwargs)

    def create_new_comment(self):

        comment = Comment.objects.create(
            owner=self.owner,
            story=self.story,
            body=self.cleaned_data['comment'],
            status=Comment.PUBLISHED)

        StoryFollow.objects.get_or_create(
            follower=comment.owner,
            target=comment.story, defaults={
                'reason': StoryFollow.REASON_COMMENTED})

        """
        Send notificationsself.
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

    def update_old_comment(self):
        comment = Comment.objects.get(id=self.comment_id)
        comment.body = self.cleaned_data['comment']
        return comment

    def save(self):
        if self.comment_id:
            return self.update_old_comment()
        else:
            return self.create_new_comment()
