from django.conf import settings
from resmin.celery_app import app

from ..follow.models import QuestionFollow
from ..notification.utils import notify
from django_redis import get_redis_connection

from resmin.utils import _set_avatar_to_answer


redis = get_redis_connection('default')

"""
TODO: Some tasks are crowded and not necessary to be there. Change them to
      correct positions when you have time.
"""


@app.task
def user_created_question_callback_task(question):
    # Make user follower of question.
    if question.owner.email and not \
       QuestionFollow.objects.filter(
            follower=question.owner, target=question).exists():
        QuestionFollow.objects.create(
            follower=question.owner, target=question,
            Nreason=QuestionFollow.ASKED)


def _update_related_question_meta_of_story(story):
    if not QuestionFollow.objects.filter(
       follower=story.owner, target=story.question_meta).exists():
        QuestionFollow.objects.create(
            follower=story.owner, target=story.question_meta,
            reason=QuestionFollow.ANSWERED)

    story.question_meta.update_follower_count()
    story.question_meta.update_answer_count()
    story.question_meta.update_updated_at()
    story.question_meta.latest_answer = story
    story.question_meta.update_follower_count()
    story.question_meta.save(
        update_fields=['answer_count', 'follower_count',
                       'updated_at', 'latest_answer'])


def _update_related_profile_of_story(story):
    profile = story.owner.profile
    profile.update_story_count()
    profile.save(update_fields=['story_count'])


def _user_created_story_callback_task(story):
    _update_related_question_meta_of_story(story)
    _update_related_profile_of_story(story)

    # If story is answer of a question notify questioner
    if story.question:
        notify(ntype_slug='user_answered_my_question',
               sub=story.question.questionee,
               obj=story.question, recipient=story.question.questioner,
               ignored_recipients=[story.owner],
               url=story.get_absolute_url())

    # If questionmeta has followers. Notify them new answers.
    meta = story.question_meta
    for follow in QuestionFollow.objects.filter(
            status=QuestionFollow.FOLLOWING, target=meta):
        notify(ntype_slug='new_answer_to_following_question',
               sub=story, obj=meta, recipient=follow.follower,
               ignored_recipients=[story.owner],
               url=meta.get_absolute_url())

    # Set avatar for user if necessary.
    if settings.AVATAR_QUESTIONMETA_ID == story.question_meta_id:
        _set_avatar_to_answer(story)


@app.task
def user_created_story_callback_task(story):
    _user_created_story_callback_task(story)


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
