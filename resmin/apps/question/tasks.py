from django.conf import settings
from resmin.celery_app import app

from apps.follow.models import QuestionFollow
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
def user_created_story_callback_task(story):

    # Update related question.
    if story.question:
        story.question.update_answer_count()
        story.question.update_updated_at()
        story.question.latest_answer = answer
        story.question.save(update_fields=['answer_count',
                                           'updated_at',
                                           'latest_answer'])

        # Make user follow to that question if necessary.
        if story.owner.email and not QuestionFollow.objects.filter(
           follower=story.owner, target=story.question).exists():
            QuestionFollow.objects.create(follower=story.owner,
                                          target=story.question,
                                          reason='answered')


    # Update related profile.
    profile = story.owner.profile
    profile.update_story_count()
    profile.save(update_fields=['story_count'])

    # Send emails to question followers if necessary.
    if settings.SEND_NOTIFICATION_EMAILS:
        _send_notification_emails_to_followers_of_question(answer)

    # Set avatar for user if necessary.
    if story.question.id == settings.AVATAR_QUESTION_ID:
        _set_avatar_to_answer(story)


@app.task
def story_like_changed_callback_task(story, **kwargs):

    # Update like count of answer.
    story.update_like_count()
    story.save(update_fields=['like_count'])

    # Update like count of user.
    profile = story.owner.profile
    profile.update_like_count()
    profile.save(update_fields=['like_count'])


@app.task
def user_deleted_story_callback_task(story):
    redis.delete(story._like_set_key())
    profile = story.owner.profile
    profile.update_like_count()
    profile.save(update_fields=['like_count'])
