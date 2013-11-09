from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from apps.question.models import Answer


class Command(BaseCommand):
    args = '<username amount...>'
    help = 'Generates given amount of '

    def handle(self, *args, **options):
        for user in User.objects.all():
            like_score = 0
            for answer in Answer.objects.filter(owner=user):
                like_score += answer.like_score
            profile = user.profile
            profile.like_score = like_score
            profile.save()
            print "updated %s like score %s" % (user, like_score)
