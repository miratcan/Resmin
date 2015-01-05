from django.dispatch import Signal, receiver

from apps.question.tasks import (story_like_changed_callback_task,
                                 user_created_question_callback_task,
                                 user_created_story_callback_task,
                                 user_deleted_story_callback_task)

story_like_changed = Signal()
user_created_question = Signal()
user_created_story = Signal()
user_deleted_story = Signal()


@receiver(story_like_changed)
def story_like_changed_callback(sender, **kwargs):
    story_like_changed_callback_task.delay(sender)


@receiver(user_created_question)
def user_created_question_callback(sender, **kwargs):
    user_created_question_callback_task.delay(sender)


@receiver(user_created_story)
def user_created_story_callback(sender, **kwargs):
    user_created_story_callback_task.delay(sender)


@receiver(user_deleted_story)
def user_deleted_story_callback(sender, **kwargs):
    user_deleted_story_callback_task.delay(sender)

