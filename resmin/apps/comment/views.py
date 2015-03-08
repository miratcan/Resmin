from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404, render
from apps.comment.models import Comment
from apps.comment.forms import UpdateCommentForm
from libs.shortcuts import render_to_json
from django.views.decorators.http import require_http_methods


def update_comment(request, cid):
    """
    TODO: This function has code duplication, clean it when you have time.
    """
    comment = get_object_or_404(Comment, id=cid, owner=request.user)
    if request.method == 'POST':
        update_comment_form = UpdateCommentForm(
            request.POST, comment=comment)
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
    return render(request, 'comments/comment.html', {
        'comment': comment})


@csrf_exempt
@require_http_methods(['POST', ])
def delete_comment(request, cid):
    comment = get_object_or_404(Comment, id=cid, owner=request.user)
    comment.status = Comment.DELETED_BY_OWNER
    comment.save()
    return render_to_json({'status': 'deleted'})
