from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

from resmin.celery_app import app

from apps.notification.models import NotificationPreference


@app.task
def notification_created_callback_task(notification):

    preference = NotificationPreference.objects.get_or_create(
        user=notification.recipient, ntype=notification.type,
        defaults={'subscription_status': 0})

    if preference.subscription_status == 1:

        # send mail to followers
        title = render_to_string(
            "notifications/%s/email_subject.txt" % notification.type.slug,
            {"notification": notification})
        body = render_to_string(
            "notifications/%s/email_body.txt" % notification.type.slug,
            {"notification": notification})

        send_mail(title, body, settings.DEFAULT_FROM_EMAIL,
            [notification.recipient.email, ])
