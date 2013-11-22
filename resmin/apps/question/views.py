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

from apps.question.models import Question, Answer

from apps.follow.models import QuestionFollow, UserFollow
from apps.follow.models import compute_blocked_user_ids_for

from apps.question.forms import (CreateQuestionForm,
                                 AnswerQuestionForm,
                                 UpdateAnswerForm,
                                 DeleteQuestionForm,
                                 SearchQuestionForm)

from django.views.decorators.csrf import csrf_exempt
from redis_cache import get_redis_connection

from utils import paginated
from utils import render_to_json

redis = get_redis_connection('default')


def build_answer_queryset(request, **kwargs):
    """
    build_answer_queryset(request)
    Returns public answers

    build_answer_queryset(request, get_from='question', question=...)
    Returns public answers from question

    build_answer_queryset(request, get_from='user', user=request.user)
    Returns public answers from user
    """

    user = request.user
    user_is_authenticated = user.is_authenticated()
    queryset = kwargs.get('queryset', Q(status=0))

    get_from = kwargs.get('get_from', None)
    get_filter = kwargs.get('get_filter', 'public')

    if get_from == 'user':
        queryset = queryset & Q(owner=kwargs.get('user'))
    elif get_from == 'question':
        queryset = queryset & Q(question=kwargs.get('question'))

    if get_filter == 'public':
        queryset = queryset & Q(visible_for=0)
    else:
        if user_is_authenticated:
            if get_filter == 'from_followings':
                queryset = queryset & Q(
                    visible_for=1, owner_id__in=user.following_user_ids)
            elif get_filter == 'to_followings':
                queryset = queryset & Q(visible_for=1)
            elif get_filter == 'direct':
                queryset = queryset & Q(
                    visible_for=2, visible_for_users=user)
        else:
            return []

    if user.is_authenticated():

        blocked_user_ids = compute_blocked_user_ids_for(user)

        if blocked_user_ids:
            queryset = queryset & ~Q(owner_id__in=blocked_user_ids)

    answers = Answer.objects\
        .filter(queryset)\
        .prefetch_related('question__owner__userprofile')\
        .select_related('question__owner__userprofile')

    return {
        'paginated_object_list': paginated(
            request, answers, settings.ANSWERS_PER_PAGE),
        'from': get_from,
        'filter': get_filter}


def index(request, **kwargs):

    answers = build_answer_queryset(request, **kwargs)

    if request.user.is_authenticated():
        pending_follow_requests = UserFollow.objects.filter(
            target=request.user, status=0).count()
    else:
        pending_follow_requests = 0

    show_email_message = request.user.is_authenticated() and \
        not request.user.email

    show_fix_answers_message = request.user.is_authenticated() and \
        Answer.objects.filter(owner=request.user,
                              status=0,
                              visible_for=None).exists()

    return render(request,
                  "index.html",
                  {'page_name': 'index',
                   'answers': answers,
                   'show_question_info_below_answers': True,
                   'show_email_message': show_email_message,
                   'show_fix_answers_message': show_fix_answers_message,
                   'pending_follow_requests': pending_follow_requests})


def question(request, base62_id, show_delete=False, **kwargs):
    question = get_object_or_404(Question, id=base62.to_decimal(base62_id))

    answers = build_answer_queryset(
        request, get_from='question', question=question, **kwargs)

    show_delete_action = question.is_deletable_by(
        request.user, answers=answers)

    delete_form = DeleteQuestionForm(
        requested_by=request.user, question=question) if show_delete_action \
        and show_delete else None

    answer_form = AnswerQuestionForm(user=request.user) if \
        question.is_answerable_by(request.user) else None

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

        # If answer requested by page
        elif request.POST.get('answer'):

            #Fill answer form with posted data and files
            answer_form = AnswerQuestionForm(
                request.POST, request.FILES, user=request.user)

            # If form is valid save answer and redirect
            if answer_form.is_valid():
                answer = answer_form.save(commit=False)
                answer.question = question
                answer.owner = request.user
                answer.save()
                answer_form.save_m2m()
                return HttpResponseRedirect(answer.get_absolute_url())
            else:
                print answer_form.errors

    return render(request, "question/question_detail.html", {
        'question': question,
        'answers': answers,
        'show_delete_action': show_delete_action,
        'answer_form': answer_form,
        'delete_form': delete_form})


def questions(request):

    search_form = SearchQuestionForm(
        initial={'q': _('Enter word(s) that you want to search in questions')})

    create_form = CreateQuestionForm(
        initial={'text': _('Submit a question')}) if \
        request.user.is_authenticated() else None

    questions = Question.objects.filter(status=0)

    if request.method == 'GET':
        search_form = SearchQuestionForm(request.GET)
        if search_form.is_valid():
            questions = questions.filter(text__search=search_form['q'])
    elif request.method == 'POST':
        create_form = CreateQuestionForm(request.POST)
        if create_form.is_valid():
            question = create_form.save(commit=False)
            question.owner = request.user
            question.save()
            return HttpResponseRedirect(question.get_absolute_url())
    questions = paginated(request, questions, settings.QUESTIONS_PER_PAGE)
    return render(request,
                  "question/question_list.html",
                  {'questions': questions,
                   'create_form': create_form,
                   'search_form': search_form,
                   'trimmed': True})


def answer(request, base62_id):
    if 'delete' in request.POST:
        answer = get_object_or_404(
            Answer, id=base62.to_decimal(base62_id), owner=request.user)

        answer.status = 1
        answer.save()

        messages.success(request, _('Your answer deleted'))
        return HttpResponseRedirect(reverse('index'))

    answer = get_object_or_404(Answer, id=base62.to_decimal(base62_id))
    answer_is_visible = answer.is_visible_for(request.user) and \
        answer.status == 0
    return render(
        request,
        'question/answer_detail.html',
        {'answer': answer,
         'answer_is_visible': answer_is_visible})


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


@login_required
def random(request):
    return HttpResponseRedirect(
        Question.objects
        .filter(status=0)
        .order_by('?')[0].get_absolute_url())


@csrf_exempt
@login_required
def like(request):

    if not request.POST:
        return HttpResponse(status=400)

    aid, v = request.POST.get('aid'), request.POST.get('v')

    if not aid:
        return HttpResponse(status=400)

    answer = get_object_or_404(Answer, id=int(aid))
    created = answer.set_like(request.user, liked=bool(int(v)))

    return HttpResponse(simplejson.dumps({'like_count': answer.like_count,
                                          'status': bool(created)}))


@login_required
def fix_answers(request):
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

    answer = get_object_or_404(Answer, owner=request.user, id=aid)

    if action in ('set_to_public', 'set_to_followings'):
        answer.visible_for = {'set_to_public': 0,
                              'set_to_followings': 1}[action]

    elif action in ('delete'):
        answer.status = 1

    answer.save()

    return render_to_json({'success': True})
