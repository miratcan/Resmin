from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from utils import _set_avatar_to_answer
from apps.question.models import QuestionMeta


class Command(BaseCommand):
    def handle(self, *args, **options):
        for user in User.objects.all():
            story = user.story_set.filter(question_meta=QuestionMeta.objects.get(id=settings.AVATAR_QUESTIONMETA_ID)).first()
            if story:
                _set_avatar_to_answer(story)
                print "avatar fixed for %s" % story.owner
