from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.mail import send_mail
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


def send_email_from_template(template_name, recipients, context):
    e_subject_path = '%s/%s_subject.txt' % (
        settings.EMAIL_TEMPLATES_PREFIX, template_name)
    e_body_path = '%s/%s_body.txt' % (
        settings.EMAIL_TEMPLATES_PREFIX, template_name)

    e_subject = render_to_string(e_subject_path, context).replace('\n', '')
    e_body = render_to_string(e_body_path, context)

    send_mail(e_subject, e_body, settings.EMAIL_FROM, recipients)


def _send_notification_emails_to_followers_of_question(new_answer):

    from follow.models import QuestionFollow

    # TODO: Check for optimisation of this query
    follows = QuestionFollow.objects\
        .filter(target=new_answer.question, status=0)\
        .exclude(follower=new_answer.owner)\
        .prefetch_related('follower__userpreference_set')

    for follow in follows:
        send_email_from_template(
            'new_answer',
            [follow.follower.email],
            {'domain': Site.objects.get_current().domain,
             'answer': new_answer,
             'follow': follow})


def _set_avatar_to_answer(answer):
    answer.owner.userprofile.avatar = answer.image
    answer.owner.userprofile.save(update_fields=['avatar'])


def render_to_json(data):
    return HttpResponse(simplejson.dumps(data),
                        content_type="application/json")
