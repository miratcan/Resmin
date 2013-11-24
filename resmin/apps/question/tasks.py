from django.conf import settings
from resmin.celery_app import app

from apps.follow.models import QuestionFollow
from apps.account.models import UserProfile
from redis_cache import get_redis_connection

from utils import (_send_notification_emails_to_followers_of_question,
                   _set_avatar_to_answer)
    

redis = get_redis_connection('default')


@app.task
def user_created_question_callback_task(question):

    # Make user follower of question.
    if question.owner.email and not \
       QuestionFollow.objects.filter(
            follower=question.owner, target=question).exists():
        QuestionFollow.objects.create(
            follower=question.owner, target=question, reason='asked')


@app.task
def user_created_answer_callback_task(answer):

    # Update related question.
    answer.question.update_answer_count()
    answer.question.update_updated_at()
    answer.question.save(update_fields=['answer_count', 'updated_at'])

    # Update related profile.
    profile = answer.owner.get_profile()
    profile.update_answer_count()
    profile.save(update_fields=['answer_count'])

    # Send emails to question followers if necessary.
    if settings.SEND_NOTIFICATION_EMAILS:
        _send_notification_emails_to_followers_of_question(answer)

    # Set avatar for user if necessary.
    if answer.question.id == settings.AVATAR_QUESTION_ID:
        _set_avatar_to_answer(answer)

    # Make user follow to that question if necessary.
    if answer.owner.email and not QuestionFollow.objects.filter(
       follower=answer.owner, target=answer.question).exists():
        QuestionFollow.objects.create(
            follower=answer.owner,
            target=answer.question,
            reason='answered')

@app.task
def answer_like_changed_callback_task(answer, **kwargs):

    # Update like count of answer.
    answer.update_like_count()
    answer.save(update_fields=['like_count'])

    # Update like count of user.
    profile = answer.owner.get_profile()
    profile.update_like_count()
    profile.save(update_fields=['like_count'])

@app.task
def user_deleted_answer_callback_task(answer):
    redis.delete(answer._like_set_key())

    profile = answer.owner.get_profile()
    profile.update_like_count()
    profile.save(update_fields=['like_count'])
