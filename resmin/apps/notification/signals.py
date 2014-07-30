from django.dispatch import Signal, receiver

from apps.notification.tasks import notification_created_callback_task

follow_request_sent = Signal()


@receiver(follow_request_sent)
def notification_created_callback(sender, **kwargs):
    notification_created_callback_task.delay(sender)
