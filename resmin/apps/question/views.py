import json

from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
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
from apps.question.forms import (RequestAnswerForm, SearchForm,
                                 ComplainQuestionMetaForm)
from apps.notification.utils import notify
from apps.follow.models import QuestionFollow

from resmin.utils import paginated

redis = get_redis_connection('default')


def index(request, listing='public'):
    """
    If user is authenticated and not registered email we will show
    Register your email message
    """
    if not request.user.is_authenticated():
        listing = 'public'
    show_email_message = request.user.is_authenticated() and \
        not request.user.email
    stories = Story.objects.build(
        requested_user=request.user, listing=listing)
    stories = paginated(request, stories, settings.STORIES_PER_PAGE)
    recommended_questions = QuestionMeta.objects\
        .filter(is_featured=True).order_by('?')[:10]
    last_registered_users = User.objects\
        .filter(is_active=True).order_by('-date_joined')[:20]
    ctx = {'stories': stories,
           'listing': listing,
           'recommended_questions': recommended_questions,
           'last_registered_users': last_registered_users,
           'show_email_message': show_email_message}
    return render(request, "index2.html", ctx)


def questions(request):

    if request.GET:
        return render(request, "question/question_meta_list.html", {})

    return render(request, "question/question_meta_list.html", {
        'search_form': SearchForm(),
        'qms': QuestionMeta.objects.filter(
            status=QuestionMeta.PUBLISHED, redirected_to=None)})


def question(request, base62_id, ordering=None, show_delete=False, **kwargs):
    qmeta = get_object_or_404(QuestionMeta, id=base62.to_decimal(base62_id))

    if qmeta.redirected_to:
        return HttpResponseRedirect(qmeta.redirected_to.get_absolute_url())

    stories = Story.objects.build(frm=qmeta, ordering=ordering)

    if not ordering:
        ordering = 'recent'

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
        'ordering': ordering,
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
           ignored_recipients=[request.user],
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


def complain_question(request, base62_id):
    qmeta = get_object_or_404(QuestionMeta, id=base62.to_decimal(base62_id))
    complain_form = ComplainQuestionMetaForm(
        qmeta=qmeta)
    descriptions = json.dumps(
        ComplainQuestionMetaForm._meta.model.DESCRIPTION_MAP)
    if request.method == "POST":
        complain_form = ComplainQuestionMetaForm(request.POST, qmeta=qmeta)
        if complain_form.is_valid():
            complain_form.save(complainer=request.user)
            messages.success(request, _('Your complaint sent to moderation.'))
            return HttpResponseRedirect(qmeta.get_absolute_url())

    return render(request, 'moderation/complain_qmeta.html', {
        'complain_form': complain_form,
        'descriptions': descriptions})
