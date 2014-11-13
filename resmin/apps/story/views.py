import re
from datetime import datetime
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.utils.translation import ugettext as _

from apps.question.models import Question, QuestionMeta
from apps.story.forms import CreateStoryForm, UpdateStoryForm
from apps.story.models import Story, Upload
from libs.baseconv import base62
from libs.shortcuts import render_to_json


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
        story.save()
        messages.success(request, _('Your story published.'))
    return HttpResponseRedirect(story.get_absolute_url())


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
    statuses_in = [Story.DRAFT, Story.PUBLISHED] if request.user.is_authenticated() \
        else [Story.PUBLISHED]
    story = get_object_or_404(Story, id=base62.to_decimal(base62_id),
                              status__in=statuses_in)
    story_is_visible = story.is_visible_for(request.user)
    return render(request, 'story/story_detail.html',
                  {'story': story, 'story_is_visible': story_is_visible})


@login_required
def create_story(request, base62_id):
    qid = request.GET.get('qid')
    mid = base62.to_decimal(base62_id)
    question = get_object_or_404(
        Question, id=qid, questionee=request.user) if qid else None
    meta = get_object_or_404(QuestionMeta, id=mid)
    if request.POST:
        # Fill answer form with posted data and files
        story_form = CreateStoryForm(request.POST,
                                     request.FILES,
                                     owner=request.user,
                                     meta=meta,
                                     question=question)

        # If form is valid save answer and redirect
        if story_form.is_valid():
            story = story_form.save(slot_data=request.POST)
            return HttpResponseRedirect(story.get_absolute_url())
    else:
        story_form = CreateStoryForm(owner=request.user, question=question,
                                     meta=meta)
    return render(request,
                  'story/create_story.html',
                  {'story_form': story_form})


def update_story(request, base62_id):
    story = get_object_or_404(Story, id=base62.to_decimal(base62_id),
                              owner=request.user)
    update_story_form = UpdateStoryForm(instance=story,
                                        requested_by=request.user)
    if request.method == "POST":
        update_story_form = UpdateStoryForm(instance=story, data=request.POST,
                                            requested_by=request.user)
        if update_story_form.is_valid():
            update_story_form.save()
            messages.success(request, _('Your story updated'))
            return HttpResponseRedirect(story.get_absolute_url())

    return render(request, 'story/update_story.html',
                  {'update_story_form': update_story_form})


def get_upload(request):
    if request.POST:
        missing_keys = filter(lambda i: i not in request.POST.keys(),
                              [u'md5sum', u'size', u'model'])
        if missing_keys:
            return render_to_json({
                'success': False, 'msg': _('md5sum and size required.')},
                HttpResponseBadRequest)
        model = Upload.MODEL_MAPPING[request.POST['model']]
        try:
            obj = model.objects.get(md5sum=request.POST['md5sum'])
            return render_to_json({'status': 'uploaded',
                                   'object': obj.serialize()})
        except model.DoesNotExist:
            pass
        upload = Upload.objects.create(md5sum=request.POST['md5sum'],
                                       size=int(request.POST['size']),
                                       model=request.POST['model'],
                                       owner=request.user)
        return render_to_json({'status': 'uploading',
                               'upload_id': upload.upload_id})
    else:
        return render_to_json({
            'success': False, 'msg': _('post method required.')},
            HttpResponseBadRequest)


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
    upload.append_data(chunk, size=chunk_size)
    if end >= upload.size:
        obj = upload.convert_to_model()
        return render_to_json({'status': 'uploaded',
                               'object': obj.serialize()})
    return render_to_json({'upload_id': upload.upload_id,
                           'status': 'uploading',
                           'offset': upload.offset})
