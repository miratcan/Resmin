from django.conf import settings
from resmin.celery_app import app
from apps.follow.models import QuestionFollow
from utils import (_send_notification_emails_to_followers_of_question,
                   _set_avatar_to_answer)

@app.task
def question_post_save_callback_task(new_question):

    if not new_question.owner.email:
        return

    if not QuestionFollow.objects.filter(
       follower=new_question.owner, target=new_question).exists():
        QuestionFollow.objects.create(
            follower=new_question.owner, target=new_question, reason='asked')

@app.task
def answer_post_save_callback_task(answer):
    answer.question.update_answers_count()
    answer.question.update_updated_at()
    answer.question.save()

    # Send emails to question followers if necessary
    if settings.SEND_NOTIFICATION_EMAILS:
        _send_notification_emails_to_followers_of_question(answer)

    # Set avatar for user if necessary
    if answer.question.id == settings.AVATAR_QUESTION_ID:
        _set_avatar_to_answer(answer)

    if answer.owner.email and not QuestionFollow.objects.filter(
       follower=answer.owner, target=answer.question).exists():
        QuestionFollow.objects.create(
            follower=answer.owner,
            target=answer.question,
            reason='answered')
