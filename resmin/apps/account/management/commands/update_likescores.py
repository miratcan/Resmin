from django.core.management.base import BaseCommand

from apps.question.models import Answer, Question
from django.contrib.auth.models import User
from redis_cache import get_redis_connection

redis = get_redis_connection('default')


class Command(BaseCommand):
    args = '<username amount...>'
    help = 'Generates given amount of '

    def handle(self, *args, **options):
        answers = Answer.objects.all()
        counter = 0
        for answer in answers:
            answer.update_like_count()
            answer.save()
            print "Updated %s/%s of answers." % (counter + 1, answers.count())
            counter += 1

        questions = Question.objects.all()
        counter = 0
        for question in questions:
            question.update_answer_count()
            question.save()
            print "Updated %s/%s of questions." % (counter + 1,
                                                   questions.count())
            counter += 1

        users = User.objects.all()
        counter = 0
        for user in users:
            userprofile = user.profile
            userprofile.update_like_count()
            userprofile.update_follower_count()
            userprofile.update_following_count()
            userprofile.update_answer_count()
            userprofile.save()
            print "Updated %s/%s of users." % (counter + 1, users.count())
            counter += 1
