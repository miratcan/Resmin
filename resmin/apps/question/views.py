import json

from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import (HttpResponseRedirect, HttpResponse)
from django.utils.translation import ugettext as _
from django.utils import simplejson
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from redis_cache import get_redis_connection

from libs.baseconv import base62
from apps.question.models import Question, QuestionMeta
from apps.story.models import Story
from apps.follow.models import QuestionFollow
from apps.follow.models import compute_blocked_user_ids_for
from apps.question.forms import (DeleteQuestionForm)
from utils import paginated


redis = get_redis_connection('default')


def build_story_queryset(request, **kwargs):
    """
    Every build has:
        Public answers,
        Answers from followings which is marked as for following_user_ids
        Answers from request.user

    build_answer_queryset(request)
    Returns public answers

    build_answer_queryset(request, get_from='question', question=...)
    Returns public answers from question

    build_answer_queryset(request, get_from='user', user=request.user)
    Returns public answers from user
    """
    user = request.user

    # Get queryset if exits
    queryset = kwargs.get(
        'queryset',
        Q(status=Story.PUBLISHED, visible_for=Story.VISIBLE_FOR_EVERYONE))

    # Get from can be user, question, and public.
    get_from = kwargs.get('get_from', None)

    # Build queryset via get_from.
    if get_from == 'user':
        queryset = queryset & \
            Q(owner=kwargs.get('user'), is_anonymouse=False)
    elif get_from == 'question':
        queryset = queryset & \
            Q(question=kwargs.get('question'))

    if user.is_authenticated():

        following_user_ids = user.following_user_ids
        following_user_ids.append(user.id)

        if get_from == 'user':
            queryset = queryset | Q(
                owner=kwargs.get('user'),
                owner_id__in=following_user_ids,
                visible_for__in=[1, 2])
        elif get_from == 'question':
            queryset = queryset | Q(
                question=kwargs.get('question'),
                owner_id__in=following_user_ids,
                visible_for__in=[1, 2])
        elif get_from == 'followings':
            queryset = Q(
                owner_id__in=following_user_ids,
                visible_for__in=[0, 1])
        else:
            queryset = queryset & Q(
                owner_id__in=following_user_ids,
                visible_for__in=[1, 2])

        blocked_user_ids = compute_blocked_user_ids_for(user)

        if blocked_user_ids:
            queryset = queryset & ~Q(owner_id__in=blocked_user_ids)

    stories = Story.objects\
        .filter(queryset)\
        .select_related('question__owner__userprofile', 'owner')
    return {
        'paginated_object_list': paginated(
            request, stories, settings.STORIES_PER_PAGE),
        'from': get_from}


@login_required
def index(request):
    '''If user is authenticated and not registered email we will show
    Register your email message'''
    show_email_message = request.user.is_authenticated() and \
        not request.user.email
    stories = build_story_queryset(request, get_from='followings')
    latest_asked_questions = QuestionMeta.objects.order_by(
        '-created_at')[:10]
    latest_answered_questions = QuestionMeta.objects.order_by(
        '-updated_at')[:10]

    return render(request,
                  "index2.html",
                  {'page_name': 'index',
                   'stories': stories,
                   'latest_asked_questions': latest_asked_questions,
                   'latest_answered_questions': latest_answered_questions,
                   'trimmed': True,
                   'show_email_message': show_email_message})


def question(request, base62_id, show_delete=False, **kwargs):
    question = get_object_or_404(QuestionMeta, id=base62.to_decimal(base62_id))

    answers = build_story_queryset(
        request, get_from='question', question=question, **kwargs)

    show_delete_action = question.is_deletable_by(
        request.user, answers=answers)

    delete_form = DeleteQuestionForm(
        requested_by=request.user, question=question) if show_delete_action \
        and show_delete else None

    # If request method is not post directly jump over render
    if request.method == 'POST' and request.user.is_authenticated():

        # If deletion requested by page
        if request.POST.get('delete'):

            # Fill delete form with Post data.
            delete_form = DeleteQuestionForm(
                request.POST, requested_by=request.user, question=question)

            # If form is valid save and redirect
            if delete_form.is_valid():
                delete_form.save()
                messages.success(request, _('Your question is deleted'))
                return HttpResponseRedirect(reverse('index'))

    return render(request, "question/question_detail.html", {
        'question': question,
        'answers': answers,
        'show_delete_action': show_delete_action,
        'delete_form': delete_form})


@login_required
def cancel_follow(request, key):

    follow = get_object_or_404(
        QuestionFollow,
        key=key,
        follower=request.user)

    follow.status = 1
    follow.save()

    return render(request,
                  'question/unsubscribe_done.html',
                  {'question': follow.target})


@csrf_exempt
def like(request):
    if not request.user.is_authenticated():
        return HttpResponse(status=401)

    # TODO: Make it decorator
    if not request.POST:
        return HttpResponse(status=400)

    aid, v = request.POST.get('aid'), request.POST.get('v')

    if not aid:
        return HttpResponse(status=400)

    answer = get_object_or_404(Story, id=int(aid))
    created = answer.set_like(request.user, liked=bool(int(v)))

    return HttpResponse(simplejson.dumps(
        {'like_count': answer.get_like_count_from_redis(),
         'status': bool(created)}))


@csrf_exempt
def follow_question(request):
    if not request.user.is_authenticated():
        return HttpResponse(status=401)

    # TODO: Make it decorator
    if not request.POST:
        return HttpResponse(status=400)

    qid, act = request.POST.get('qid'), request.POST.get('a')

    if not qid:
        return HttpResponse(status=400)

    if act not in ['follow', 'unfollow']:
        return HttpResponse(status=400)

    question = get_object_or_404(Question, id=int(qid))

    if act == 'follow':
        qf = QuestionFollow.objects.get_or_create(follower=request.user,
                                                  target=question)[0]

        if not qf.status == 0:
            qf.reason = 'followed'
            qf.status = 0
            qf.save(update_fields=['reason', 'status'])

        is_following = True

    elif act == 'unfollow':

        try:
            qf = QuestionFollow.objects.get(id=qid)
        except:
            qf = None

        if qf:
            qf.status = 1
            qf.save(update_fields=['status'])

        is_following = False

    return HttpResponse(json.dumps({'is_following': is_following}))
