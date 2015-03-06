from django.shortcuts import get_object_or_404, render_to_response, render
from apps.comment.models import Comment
from apps.comment.forms import UpdateCommentForm

def update_comment(request, cid):
    comment = get_object_or_404(Comment, id=cid, owner=request.user)
    if request.method == 'POST':
        update_comment_form = UpdateCommentForm(request.POST, comment=comment)
        if update_comment_form.is_valid():
            update_comment_form.save()
            return render(request, 'comments/comment.html', {
                'comment': comment})
    else:
        update_comment_form = UpdateCommentForm(comment=comment)
    return render(request, 'comments/update_form.html', {
        'update_comment_form': update_comment_form})

def get_comment(request, cid):
    comment = get_object_or_404(Comment, id=cid, owner=request.user)
    return render_to_response('comments/comment.html', {
        'comment': comment})
