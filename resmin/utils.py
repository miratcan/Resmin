from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.mail import send_mail
from django.utils.translation import ugettext as _
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.contrib.sites.models import Site
from django.conf import settings
from django.utils import simplejson

import os
import uuid
import datetime


def unique_filename(instance, filename, prefix):
    f, ext = os.path.splitext(filename)
    n = datetime.datetime.now()
    return '%s/%s/%s/%s/%s%s' % (prefix,
                                 n.year,
                                 n.month,
                                 n.day,
                                 uuid.uuid4().hex,
                                 ext)


def unique_filename_for_answer(instance, filename):
    return unique_filename(instance, filename, 'answers')


def unique_filename_for_avatar(instance, filename):
    return unique_filename(instance, filename, 'avatars')


def paginated(request, query, amount):

    paginator = Paginator(query, amount)
    page = request.GET.get('page')

    try:
        objects = paginator.page(page)
    except PageNotAnInteger:
        objects = paginator.page(1)
    except EmptyPage:
        objects = paginator.page(paginator.num_pages)

    return objects


def _send_notification_emails_to_followers_of_question(new_answer):

    from follow.models import QuestionFollow

    titles = {'asked': _('A question that you asked has a new answer'),
              'answered': _('A question that you answered before has '
                            'new answer')}

    follows = QuestionFollow.objects\
        .filter(target=new_answer.question, status=0)\
        .exclude(follower=new_answer.owner)

    for follow in follows:
        email_ctx = render_to_string(
            'emails/new_answer_body.txt', {
                'domain': Site.objects.get_current().domain,
                'answer': new_answer,
                'follow': follow})
        send_mail(titles[follow.reason],
                  email_ctx,
                  settings.EMAIL_FROM,
                  [follow.follower.email],
                  fail_silently=False)


def _set_avatar_to_answer(answer):
    answer.owner.avatar = answer.image
    answer.owner.save()


def render_to_json(data):
    return HttpResponse(simplejson.dumps(data),
                        content_type="application/json")
