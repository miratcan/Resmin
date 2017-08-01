from django.dispatch import Signal, receiver

from .tasks import (follow_request_sent_callback_task,
                             follower_count_changed_callback_task,
                                following_count_changed_callback_task)


follow_request_sent = Signal()
follow_request_received = Signal()
follower_count_changed = Signal()
following_count_changed = Signal()


@receiver(follow_request_sent)
def follow_request_sent_callback(sender, **kwargs):
    follow_request_sent_callback_task.delay(sender)


@receiver(follower_count_changed)
def follower_count_changed_callback(sender, **kwargs):
    follower_count_changed_callback_task.delay(sender)


@receiver(follower_count_changed)
def following_count_changed_callback(sender, **kwargs):
    following_count_changed_callback_task.delay(sender)
