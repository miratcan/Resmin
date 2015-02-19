import json

from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import (HttpResponse, HttpResponseBadRequest,
                         HttpResponseRedirect)
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from django.utils.translation import ugettext as _
from redis_cache import get_redis_connection

from libs.baseconv import base62
from libs.shortcuts import render_to_json
from apps.story.models import Story
from apps.question.models import Question, QuestionMeta
from apps.question.forms import RequestAnswerForm
from apps.notification.utils import notify
from apps.follow.models import QuestionFollow, compute_blocked_user_ids_for

from libs.shortcuts import render_to_json
from utils import paginated

redis = get_redis_connection('default')


def _index(request, stories, extra):
    """
    If user is authenticated and not registered email we will show
    Register your email message
    """
    show_email_message = request.user.is_authenticated() and \
        not request.user.email
    stories = paginated(request, stories, settings.STORIES_PER_PAGE)
    recommended_questions = QuestionMeta.objects.\
        filter(is_featured=True).order_by('?')[:10]
    ctx = {'stories': stories,
           'recommended_questions': recommended_questions,
           'show_email_message': show_email_message}
    if extra:
        ctx.update(extra)
    return render(request, "index2.html", ctx)


@login_required
def index_wall(request):
    """
    Show public posts from following users.
    """
    blocked_user_ids = compute_blocked_user_ids_for(request.user)
    stories = Story.objects\
        .filter(status=Story.PUBLISHED,
                visible_for=Story.VISIBLE_FOR_EVERYONE,
                owner_id__in=request.user.following_user_ids)\
        .exclude(owner_id__in=blocked_user_ids)
    return _index(request, stories,
                  extra={'from': 'followings'})


def index_public(request):
    """
    Show public posts from everyone
    """
    stories = Story.objects\
        .filter(status=Story.PUBLISHED, visible_for=Story.VISIBLE_FOR_EVERYONE)
    if request.user.is_authenticated():
        blocked_user_ids = compute_blocked_user_ids_for(request.user)
        stories = stories.exclude(owner_id__in=blocked_user_ids)
    else:
        stories = stories.exclude(is_nsfw=True)
    return _index(request, stories, extra={'from': 'public'})


@login_required
def index_private(request):
    """
    Show private posts from users that request.user is
    following.
    """
    blocked_user_ids = compute_blocked_user_ids_for(request.user)
    following_user_ids = request.user.following_user_ids
    stories = Story.objects\
        .filter(status=Story.PUBLISHED,
                visible_for=Story.VISIBLE_FOR_FOLLOWERS,
                owner_id__in=following_user_ids)
    if blocked_user_ids:
        stories = stories.exclude(owner_id__in=blocked_user_ids)
    return _index(request, stories,
                  extra={'from': 'private'})


def index(request):
    if request.user.is_authenticated():
        return index_wall(request)
    else:
        return index_public(request)


def questions(request):
    qms = QuestionMeta.objects.filter(status=QuestionMeta.PUBLISHED)\
                              .order_by('-is_sponsored', '-is_featured',
                                        'answer_count')
    return render(request, "question/question_meta_list.html", {
        'qms': qms})


def question(request, base62_id, order=None, show_delete=False, **kwargs):
    qmeta = get_object_or_404(QuestionMeta,
                              id=base62.to_decimal(base62_id))

    order = {'popular': '-like_count',
             'featured': 'is_featured',
             'recent': '-created_at'}.get(order, '-created_at')

    stories = Story.objects\
        .from_question_meta(qmeta)\
        .filter(status=Story.PUBLISHED,
                visible_for=Story.VISIBLE_FOR_EVERYONE).order_by(order)

    if request.user.is_authenticated():
        request_answer_form = RequestAnswerForm(questioner=request.user,
                                                qmeta=qmeta)
        if request.method == 'POST':
            request_answer_form = RequestAnswerForm(
                request.POST, questioner=request.user, qmeta=qmeta,)
            if request_answer_form.is_valid():
                usernames = request_answer_form.save()
                if usernames:
                    messages.success(request, 'Your question sent to: %s' %
                                              ', '.join(usernames))
                else:
                    messages.error(request, 'Could\'t find any users to send.')
                return HttpResponseRedirect(qmeta.get_absolute_url())
    else:
        request_answer_form = None

    if request.user.is_authenticated():
        is_following = QuestionFollow.objects\
            .filter(target=qmeta,
                    follower=request.user,
                    status=QuestionFollow.FOLLOWING).exists()
    else:
        is_following = False

    return render(request, "question/question_detail.html", {
        'question': qmeta,
        'is_following': is_following,
        'request_answer_form': request_answer_form,
        'stories': paginated(request, stories, settings.STORIES_PER_PAGE)})


@csrf_exempt
def like(request):
    if not request.user.is_authenticated():
        return render_to_json(
            {'errMsg': _('You have to login to complete this action.')},
            HttpResponse, 401)

    # TODO: Make it decorator
    if not request.POST:
        return render_to_json(
            {'errMsg': _('You have send bad data.')},
            HttpResponse, 400)

    sid, val = request.POST.get('sid'), request.POST.get('val')

    if not sid:
        return HttpResponse(status=400)

    story = get_object_or_404(Story, id=int(sid))
    is_liked = story.set_like(request.user, liked=bool(int(val)))
    notify(ntype_slug='user_liked_my_answer',
           sub=request.user,
           obj=story,
           recipient=story.owner,
           url=story.get_absolute_url())
    like_count = story.get_like_count_from_redis()
    return HttpResponse(json.dumps(
        {'like_count': like_count,
         'is_liked': is_liked}))


@login_required
def pending_question_action(request):
    def _reject(question):
        question.status = Question.REJECTED
        question.save()
        return render_to_json({'qpk': question.pk,
                               'status': question.status})

    qpk, action = request.POST.get('qpk'), request.POST.get('action')
    question = get_object_or_404(Question, pk=qpk, questionee=request.user)
    action_method = {'reject': _reject}.get(action)
    if action_method:
        return action_method(question)
    else:
        return render_to_json({'errMsg': _('Action not found')},
                              HttpResponseBadRequest)


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

    qid = int(qid)
    meta = get_object_or_404(QuestionMeta, id=qid)

    if act == 'follow':
        qf = QuestionFollow.objects.get_or_create(
            follower=request.user, target=meta, defaults={
                'reason': QuestionFollow.FOLLOWED})[0]

        if not qf.status == QuestionFollow.FOLLOWING:
            qf.reason = QuestionFollow.FOLLOWED
            qf.status = QuestionFollow.FOLLOWING
            qf.save(update_fields=['reason', 'status'])
            qf.target.update_follower_count()
            qf.target.save(update_fields=['follower_count'])

        is_following = True

    elif act == 'unfollow':

        try:
            qf = QuestionFollow.objects.get(
                follower=request.user, target_id=qid)
        except QuestionFollow.DoesNotExist:
            qf = None

        if qf:
            qf.status = QuestionFollow.UNFOLLOWED
            qf.save(update_fields=['status'])
            qf.target.update_follower_count()
            qf.target.save(update_fields=['follower_count'])

        is_following = False

    return HttpResponse(json.dumps({
        'is_following': is_following,
        'follower_count': qf.target.follower_count}))
