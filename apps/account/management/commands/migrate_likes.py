from django.core.management.base import BaseCommand
from apps.question.models import BaseModel, Answer
from django.db import models
from redis_cache import get_redis_connection

redis = get_redis_connection('default')


class Like(BaseModel):
    answer = models.ForeignKey(Answer)

    class Meta:
        db_table = 'question_like'


class Command(BaseCommand):
    args = '<username amount...>'
    help = 'Generates given amount of '

    def handle(self, *args, **options):

        redis.flushall()

        for answer in Answer.objects.filter(status=0):
            print "Migrating likes for answer: %s" % answer
            print
            likes = Like.objects.filter(answer=answer)
            total_likes = 0
            for like in likes:
                result = answer.set_like(like.owner)
                if result:
                    print "\tlike:%s migrated" % like.owner
                    total_likes += 1
                else:
                    print "\tlike:%s duplicated" % like.owner

            print "\tTotal likes: %s" % total_likes
            print
