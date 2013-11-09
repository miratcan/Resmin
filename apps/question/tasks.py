from django.conf import settings

from celery import task

from apps.follow.models import QuestionFollow


@task()
def new_question_handler(new_question):

    if not new_question.owner.email:
        return

    if not QuestionFollow.objects.filter(
       follower=new_question.owner, target=new_question).exists():
        QuestionFollow.objects.create(
            follower=new_question.owner, target=new_question, reason='asked')


@task()
def new_answer_handler(new_answer):
    from utils import (_send_notification_emails_to_followers_of_question,
                       _set_avatar_to_answer)

    # Send emails to question followers if necessary
    if settings.SEND_NOTIFICATION_EMAILS:
        _send_notification_emails_to_followers_of_question(new_answer)

    # Set avatar for user if necessary
    if new_answer.question.id == settings.AVATAR_QUESTION_ID:
        _set_avatar_to_answer(new_answer)

    # If user is not following related question, create a follow
    if not new_answer.owner.email:
        return

    if not QuestionFollow.objects.filter(
       follower=new_answer.owner, target=new_answer.question).exists():
        QuestionFollow.objects.create(
            follower=new_answer.owner,
            target=new_answer.question,
            reason='answered')
