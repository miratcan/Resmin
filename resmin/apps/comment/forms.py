from django import forms

from apps.notification.utils import notify
from apps.comment.models import Comment


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

    def save(self):
        if self.comment_id:
            comment = Comment.objects.get(id=self.comment_id)
            comment.body = self.cleaned_data['comment']
        else:
            comment = Comment.objects.create(
                owner=self.owner,
                story=self.story,
                body=self.cleaned_data['comment'],
                status=Comment.PUBLISHED)
            notify(ntype_slug='new_comment_on_my_story',
                   sub=comment,
                   obj=comment.story,
                   recipient=comment.story.owner,
                   url=comment.story.get_absolute_url())
        return comment
