from django.core.management.base import BaseCommand

from apps.question.models import Answer
from apps.account.models import UserProfile
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

        userprofiles = UserProfile.objects.all()
        counter = 0
        for userprofile in userprofiles:
            userprofile.update_like_count()
            userprofile.update_follower_count()
            userprofile.update_answer_count()
            userprofile.save()
            print "Updated %s/%s of users." % (counter + 1, userprofiles.count())
            counter += 1