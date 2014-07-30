from django.shortcuts import get_object_or_404
from django.shortcuts import render

from django.core.urlresolvers import reverse

from django.db.models import Q

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods


from django.http import (HttpResponseRedirect, HttpResponse)

from django.utils.translation import ugettext as _
from django.utils import simplejson

from django.conf import settings

from libs.baseconv import base62

from apps.question.models import Question, Answer, AnswerRequest
from apps.follow.models import QuestionFollow
from apps.follow.models import compute_blocked_user_ids_for

from apps.question.forms import (AnswerQuestionForm,
                                 UpdateAnswerForm,
                                 DeleteQuestionForm)

from django.views.decorators.csrf import csrf_exempt
from redis_cache import get_redis_connection

from utils import paginated
from utils import render_to_json

redis = get_redis_connection('default')


def build_answer_queryset(request, **kwargs):
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
    queryset = kwargs.get('queryset', Q(status=0, visible_for=0))

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

    answers = Answer.objects\
        .filter(queryset)\
        .prefetch_related('question__owner__userprofile')\
        .select_related('question__owner__userprofile', 'owner')
    return {
        'paginated_object_list': paginated(
            request, answers, settings.ANSWERS_PER_PAGE),
        'from': get_from}


@login_required
def index(request):
    '''If user is authenticated and not registered email we will show
    Register your email message'''
    show_email_message = request.user.is_authenticated() and \
        not request.user.email

    '''If user is authenticated and has unfixed answers we will show
    Fix your answers message'''
    show_fix_answers_message = request.user.is_authenticated() and \
        Answer.objects.filter(owner=request.user,
                              status=0,
                              visible_for=None).exists()

    answers = build_answer_queryset(request, get_from='followings')
    latest_asked_questions = Question.objects.order_by('-created_at')[:10]
    latest_answered_questions = Question.objects.order_by('-updated_at')[:10]
    return render(request,
                  "index2.html",
                  {'page_name': 'index',
                   'answers': answers,
                   'latest_asked_questions': latest_asked_questions,
                   'latest_answered_questions': latest_answered_questions,
                   'trimmed': True,
                   'show_email_message': show_email_message,
                   'show_fix_answers_message': show_fix_answers_message})


def question(request, base62_id, show_delete=False, **kwargs):
    question = get_object_or_404(Question, id=base62.to_decimal(base62_id))

    answers = build_answer_queryset(
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


def answer(request, base62_id):
    if 'delete' in request.POST:
        answer = get_object_or_404(
            Answer, id=base62.to_decimal(base62_id), owner=request.user)

        # TODO: Create DeleteAnswerForm and move these 4 lines
        # to save method.
        from apps.question.signals import user_deleted_answer
        answer.status = 1
        answer.save()
        user_deleted_answer.send(sender=answer)

        messages.success(request, _('Your answer deleted'))
        return HttpResponseRedirect(reverse('index'))

    answer = get_object_or_404(Answer, id=base62.to_decimal(base62_id))

    if 'set_cover' in request.POST:
        answer.question.cover_answer = answer
        answer.question.save()
        messages.success(request, _('Updated Cover Image'))
        return HttpResponseRedirect(answer.get_absolute_url())

    answer_is_visible = answer.is_visible_for(request.user) and \
        answer.status == 0

    return render(
        request,
        'question/answer_detail.html',
        {'answer': answer,
         'answer_is_visible': answer_is_visible})


@login_required
def create_answer(request, question_base62_id):
    rid = request.GET.get('rid')
    qid = base62.to_decimal(question_base62_id)
    question = get_object_or_404(Question, id=qid, status=0)
    answer_request = get_object_or_404(
        AnswerRequest, id=rid, questionee=request.user) if rid else None

    answer_form = AnswerQuestionForm(
        owner=request.user, question=question,
        answer_request=answer_request)

    if request.POST:
        # Fill answer form with posted data and files
        answer_form = AnswerQuestionForm(request.POST,
                                         request.FILES,
                                         owner=request.user,
                                         question=question,
                                         answer_request=answer_request)

        # If form is valid save answer and redirect
        if answer_form.is_valid():
            answer = answer_form.save(question=question)
            return HttpResponseRedirect(answer.get_absolute_url())

    return render(request,
                  'question/create_answer.html',
                  {'answer_form': answer_form})


def update_answer(request, base62_id):
    answer = get_object_or_404(Answer,
                               id=base62.to_decimal(base62_id),
                               owner=request.user)

    update_answer_form = UpdateAnswerForm(instance=answer,
                                          requested_by=request.user)

    if request.method == "POST":
        update_answer_form = UpdateAnswerForm(instance=answer,
                                              data=request.POST,
                                              requested_by=request.user)
        if update_answer_form.is_valid():
            update_answer_form.save()
            messages.success(request, _('Your answer updated'))
            return HttpResponseRedirect(answer.get_absolute_url())

    return render(
        request,
        'question/update_answer.html',
        {'update_answer_form': update_answer_form})


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

    answer = get_object_or_404(Answer, id=int(aid))
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

    return HttpResponse(simplejson.dumps({'is_following': is_following}))


@login_required
def fix_answers(request):
    if request.user.is_superuser:
        answers = Answer.objects.filter(status=0, visible_for=None)
    else:
        answers = Answer.objects.filter(
            owner=request.user, status=0, visible_for=None)

    return render(
        request,
        'question/fix_answers.html',
        {'answers': answers})


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def fix_answer(request):
    aid = request.POST.get('aid')
    action = request.POST.get('action')

    if not action in ('set_to_public', 'set_to_followings', 'delete'):
        return render_to_json({'success': False})

    if request.user.is_superuser:
        answer = get_object_or_404(Answer, id=aid)
    else:
        answer = get_object_or_404(Answer, owner=request.user, id=aid)

    if action in ('set_to_public', 'set_to_followings'):
        answer.visible_for = {'set_to_public': 0,
                              'set_to_followings': 1}[action]

    elif action in ('delete'):
        answer.status = 1

    answer.save()

    return render_to_json({'success': True})
