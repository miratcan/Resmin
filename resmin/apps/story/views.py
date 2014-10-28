from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils.translation import ugettext as _

from apps.question.models import Question, QuestionMeta
from apps.story.forms import CreateStoryForm, UpdateStoryForm
from apps.story.models import Story
from libs.baseconv import base62


def story(request, base62_id):
    if 'delete' in request.POST:
        story = get_object_or_404(
            Story, id=base62.to_decimal(base62_id), owner=request.user)

        """
        TODO: Create DeleteAnswerForm and move these 4 lines
        to save method.
        """

        from apps.question.signals import user_deleted_answer
        story.status = 1
        story.save()
        user_deleted_answer.send(sender=story)

        messages.success(request, _('Your answer deleted'))
        return HttpResponseRedirect(reverse('index'))

    story = get_object_or_404(Story, id=base62.to_decimal(base62_id))

    if 'set_cover' in request.POST:
        story.question.cover_answer = story
        story.question.save()
        messages.success(request, _('Updated Cover Image'))
        return HttpResponseRedirect(story.get_absolute_url())

    answer_is_visible = story.is_visible_for(request.user) and \
        story.status == 0

    return render(
        request,
        'story/story_detail.html',
        {'story': story,
         'answer_is_visible': answer_is_visible})


@login_required
def create_story(request, base62_id):
    qid = request.GET.get('qid')
    mid = base62.to_decimal(base62_id)
    question = get_object_or_404(
        Question, id=qid, questionee=request.user) if qid else None
    meta = get_object_or_404(QuestionMeta, id=mid)

    story_form = CreateStoryForm(owner=request.user, question=question,
                                 meta=meta)

    if request.POST:
        # Fill answer form with posted data and files
        story_form = CreateStoryForm(request.POST,
                                     request.FILES,
                                     owner=request.user,
                                     meta=meta,
                                     question=question)

        # If form is valid save answer and redirect
        if story_form.is_valid():
            story = story_form.save()
            return HttpResponseRedirect(story.get_absolute_url())

    return render(request,
                  'story/create_story.html',
                  {'story_form': story_form})


def update_story(request, base62_id):
    story = get_object_or_404(Story, id=base62.to_decimal(base62_id),
                              owner=request.user)

    update_story_form = UpdateStoryForm(instance=story,
                                        requested_by=request.user)

    if request.method == "POST":
        update_story_form = UpdateStoryForm(instance=story,
                                             data=request.POST,
                                             requested_by=request.user)
        if update_story_form.is_valid():
            update_story_form.save()
            messages.success(request, _('Your story updated'))
            return HttpResponseRedirect(story.get_absolute_url())

    return render(
        request,
        'story/update_story.html',
        {'update_story_form': update_story_form})
