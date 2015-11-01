import re
from datetime import datetime
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.utils.translation import ugettext as _
from apps.question.models import Question, QuestionMeta
from apps.question.signals import user_created_story
from apps.comment.models import Comment
from apps.comment.forms import CommentForm
from apps.story.forms import StoryForm, UpdateCaptionsForm
from apps.story.models import Story, Upload, Image, Video
from apps.notification.decorators import delete_notification

from resmin.libs.baseconv import base62
from resmin.libs.shortcuts import render_to_json
from resmin.utils import paginated


def _delete_story(request, story=None):
    from apps.question.signals import user_deleted_story
    story.status = Story.DELETED_BY_OWNER
    story.save()
    user_deleted_story.send(sender=story)
    messages.success(request, _('Your story deleted.'))
    return HttpResponseRedirect(reverse('index'))


def _publish_story(request, story):
    if story.status == Story.DRAFT:
        story.status = Story.PUBLISHED
        story.created_at = datetime.now()
        story.save(update_fields=['status', 'created_at'])
        if story.question:
            story.question.status = Question.ANSWERED
            story.question.answer = story
            story.question.save(update_fields=['status', 'answer'])
        messages.success(request, _('Your story published.'))
        user_created_story.send(sender=story)
    return HttpResponseRedirect(story.get_absolute_url())


@delete_notification
def story(request, base62_id):
    action_keys = filter(lambda i: i in ['delete', 'publish'], request.POST)
    action_key = action_keys[0] if action_keys else None
    if action_key:
        method = {u'delete': _delete_story,
                  u'publish': _publish_story}.get(action_key)
        if method:
            story = get_object_or_404(Story, id=base62.to_decimal(base62_id),
                                      owner=request.user)
            return method(request, story)
    statuses_in = [Story.DRAFT, Story.PUBLISHED] if \
        request.user.is_authenticated() else [Story.PUBLISHED]
    story = get_object_or_404(Story, id=base62.to_decimal(base62_id),
                              status__in=statuses_in, owner__is_active=True)
    blocked_user_ids = request.user.blocked_user_ids
    story_is_visible = story.is_visible_for(request.user,
                                            blocked_user_ids=blocked_user_ids)
    comments = Comment.objects\
        .filter(story=story, status=Comment.PUBLISHED, owner__is_active=True)\
        .exclude(owner_id__in=blocked_user_ids)\
        .select_related('owner__profile')
    comments = paginated(request, comments, settings.COMMENTS_PER_PAGE)
    if request.user.is_authenticated():
        if request.method == 'POST' and request.POST.get('action') ==\
           'create_comment':
            comment_form = CommentForm(request.POST, owner=request.user,
                                       story=story)
            if comment_form.is_valid():
                comment = comment_form.save()
                return HttpResponseRedirect(comment.get_absolute_url())
        else:
            comment_form = CommentForm(owner=request.user, story=story)
    else:
        comment_form = None
    return render(request, 'story/story_detail.html',
                  {'story': story, 'current_site': Site.objects.get_current(),
                   'story_is_visible': story_is_visible, 'comments': comments,
                   'comment_form': comment_form})


@login_required
def create_story(request, base62_id):
    mid = base62.to_decimal(base62_id)
    meta = get_object_or_404(QuestionMeta, id=mid)
    if request.POST:
        story_form = StoryForm(request.POST, owner=request.user, meta=meta)
        if story_form.is_valid():
            story = story_form.save()
            return HttpResponseRedirect(story.get_absolute_url())
    else:
        story_form = StoryForm(owner=request.user, meta=meta, initial={
            'question': request.GET.get('qid')})
    return render(request, 'story/create_story.html',
                  {'story_form': story_form})


@login_required
def update_story(request, base62_id):
    story = get_object_or_404(Story, id=base62.to_decimal(base62_id),
                              owner=request.user)
    if request.method == "POST":
        story_form = StoryForm(request.POST, instance=story,
                               owner=request.user, meta=story.question_meta)
        if story_form.is_valid():
            story_form.save()
            messages.success(request, _('Your story updated'))
            return HttpResponseRedirect(story.get_absolute_url())
        else:
            return render(request, 'story/create_story.html',
                          {'story_form': story_form})
    story_form = StoryForm(instance=story, owner=request.user,
                           meta=story.question_meta)
    return render(request, 'story/create_story.html',
                  {'story_form': story_form})


@login_required
def update_details(request, base62_id):
    story = get_object_or_404(Story, id=base62.to_decimal(base62_id),
                              owner=request.user)
    if request.method == "POST":
        update_captions_form = UpdateCaptionsForm(request.POST, story=story)
        if update_captions_form.is_valid():
            update_captions_form.save(slot_data=request.POST)
            return HttpResponseRedirect(story.get_absolute_url())
    update_captions_form = UpdateCaptionsForm(story=story)
    return render(request, 'story/update_captions.html',
                  {'captions_form': update_captions_form})


def get_upload(request):
    if request.POST:
        missing_keys = filter(lambda i: i not in request.POST.keys(),
                              [u'md5sum', u'size'])

        if missing_keys:
            return render_to_json({
                'success': False, 'msg': _('md5sum and size required.')},
                status=400)

        if int(request.POST['size']) > settings.MAXIMUM_UPLOAD_SIZE:
            return render_to_json({
                'success': False, 'msg': _('File is too big to upload.')},
                status=400)

        for model in [Image, Video]:
            try:
                obj = model.objects.get(md5sum=request.POST['md5sum'])
                return render_to_json({'status': 'uploaded',
                                       'object': obj.serialize()})
            except model.DoesNotExist:
                pass

        upload = Upload.objects.create(md5sum=request.POST['md5sum'],
                                       size=int(request.POST['size']),
                                       owner=request.user)

        return render_to_json({'status': 'uploading',
                               'upload_id': upload.upload_id})
    else:
        return render_to_json({
            'success': False, 'msg': _('post method required.')},
            status=400)


CONTENT_RANGE_PATTERN = re.compile(
    r'^bytes (?P<start>\d+)-(?P<end>\d+)/(?P<total>\d+)$'
)


def upload(request, upload_id):
    """
    Get upload_id, content-range.

    IF Content Range start is not upload offset raise Error.
    Append chunk.

    IF file finished return obj.
    """
    upload = get_object_or_404(Upload, upload_id=upload_id,
                               owner=request.user,
                               expires_at__gte=datetime.now())
    chunk = request.body
    content_range = request.META.get('HTTP_CONTENT_RANGE', '')
    match = CONTENT_RANGE_PATTERN.match(content_range)

    if not match:
        return HttpResponseBadRequest('Content Range header required.')

    start = int(match.group('start'))
    end = int(match.group('end'))

    if upload.offset != start:
        return HttpResponseBadRequest('Offsets does not match.')

    chunk_size = end - start
    try:
        upload.append_data(chunk, size=chunk_size)
    except Exception as err:
        return render_to_json({'status': 'failed',
                               'msg': err.status}, status=400)

    if end >= upload.size:
        obj = upload.convert_to_model()
        return render_to_json({'status': 'uploaded',
                               'object': obj.serialize()})
    return render_to_json({'upload_id': upload.upload_id,
                           'status': 'uploading',
                           'offset': upload.offset})
