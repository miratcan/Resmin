import os
import uuid
import datetime

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.contenttypes.models import ContentType
from django.conf import settings


def unique_filename(instance, filename, prefix):
    f, ext = os.path.splitext(filename)
    n = datetime.datetime.now()
    # TODO: use os.path.join
    return '%s/%s/%s/%s%s' % (prefix, n.year, n.month, uuid.uuid4().hex, ext)


def filename_for_avatar(instance, filename):
    return unique_filename(instance, filename, 'avatars')


def filename_for_image(instance, filename):
    return unique_filename(instance, filename, 'story/images')


def filename_for_video(instance, filename):
    return unique_filename(instance, filename, 'story/videos')


def filename_for_video_frame(instance, filename):
    return '%s.jpg' % filename_for_video(instance, filename)


def generate_upload_id():
    return uuid.uuid4().hex


def filename_for_upload(instance, fn):
    return os.path.join('uploading/%s' % instance.upload_id)


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


def _set_avatar_to_answer(story):

    from apps.story.models import Image

    cTp = ContentType.objects.get_for_model(Image)
    slot = story.slot_set.filter(cTp=cTp).reverse().first()
    story.owner.userprofile.avatar = slot.content.image
    story.owner.userprofile.save(update_fields=['avatar'])

