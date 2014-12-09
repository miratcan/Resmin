import json

from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import simplejson
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from redis_cache import get_redis_connection

from libs.baseconv import base62
from apps.question.models import Question, QuestionMeta
from apps.story.models import Story
from apps.follow.models import QuestionFollow
from utils import paginated


redis = get_redis_connection('default')


@login_required
def index(request):
    '''If user is authenticated and not registered email we will show
    Register your email message'''
    show_email_message = request.user.is_authenticated() and \
        not request.user.email
    stories = Story.objects.from_followings(request.user)
    latest_asked_questions = QuestionMeta.objects.order_by(
        '-created_at')[:10]
    latest_answered_questions = QuestionMeta.objects.order_by(
        '-updated_at')[:10]

    return render(request,
                  "index2.html",
                  {'page_name': 'index',
                   'stories': paginated(request, stories,
                                        settings.STORIES_PER_PAGE),
                   'latest_asked_questions': latest_asked_questions,
                   'latest_answered_questions': latest_answered_questions,
                   'show_email_message': show_email_message})


def question(request, base62_id, show_delete=False, **kwargs):
    question = get_object_or_404(QuestionMeta,
                                 id=base62.to_decimal(base62_id))
    stories = Story.objects.from_question_meta(question)
    return render(request, "question/question_detail.html", {
        'question': question,
        'stories': paginated(request, stories, settings.STORIES_PER_PAGE)})


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
