from django.conf import settings
from resmin.celery_app import app

from apps.follow.models import QuestionFollow
from apps.notification.utils import notify
from redis_cache import get_redis_connection

from utils import _set_avatar_to_answer


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


def _update_related_question_metas_of_story(story, qms=False):

    if not qms:
        qms = story.mounted_question_metas.all()

    for qm in qms:
        if not QuestionFollow.objects.filter(
           follower=story.owner, target=qm).exists():
            QuestionFollow.objects.create(
                follower=story.owner, target=qm,
                reason=QuestionFollow.ANSWERED)

        qm.update_follower_count()
        qm.update_answer_count()
        qm.update_updated_at()
        qm.latest_answer = story
        qm.update_follower_count()
        qm.save(update_fields=['answer_count', 'follower_count',
                               'updated_at', 'latest_answer'])


def _update_related_profile_of_story(story):
    profile = story.owner.profile
    profile.update_story_count()
    profile.save(update_fields=['story_count'])


def _user_created_story_callback_task(story):
    _update_related_question_metas_of_story(story)
    _update_related_profile_of_story(story)

    # If story is answer of a question notify questioner
    if story.question:
        notify(ntype_slug='user_answered_my_question',
               sub=story.question.questionee,
               obj=story.question, recipient=story.question.questioner,
               ignored_recipients=[story.owner],
               url=story.get_absolute_url())

    # If questionmeta has followers. Notify them new answers.
    for meta in story.mounted_question_metas.all():
        for follow in QuestionFollow.objects.filter(
                status=QuestionFollow.FOLLOWING, target=meta):
            notify(ntype_slug='new_answer_to_following_question',
                   sub=story, obj=meta, recipient=follow.follower,
                   ignored_recipients=[story.owner],
                   url=meta.get_absolute_url())

    # Set avatar for user if necessary.
    qm_pks = (d['pk'] for d in story.mounted_question_metas.values('pk'))
    if settings.AVATAR_QUESTIONMETA_ID in qm_pks:
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
