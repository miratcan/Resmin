from django.dispatch import Signal, receiver

from apps.question.tasks import (answer_like_changed_callback_task,
	                             user_created_question_callback_task,
	                             user_created_answer_callback_task,
	                             user_deleted_answer_callback_task)

answer_like_changed = Signal()
user_created_question = Signal()
user_created_answer = Signal()
user_deleted_answer = Signal()

@receiver(answer_like_changed)
def answer_like_changed_callback(sender, **kwargs):
    answer_like_changed_callback_task.delay(sender)

@receiver(user_created_question)
def user_created_question_callback(sender, **kwargs):
	user_created_question_callback_task.delay(sender)

@receiver(user_created_answer)
def user_created_answer_callback(sender, **kwargs):
	user_created_answer_callback_task.delay(sender)

@receiver(user_deleted_answer)
def user_deleted_answer_callback(sender, **kwargs):
	user_deleted_answer_callback_task.delay(sender)
