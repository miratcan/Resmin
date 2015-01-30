from apps.comment.models import Comment
from django import forms


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
        return comment