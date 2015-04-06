from django.core.management.base import BaseCommand, CommandError
from urllib2 import urlparse
from libs.baseconv import base62
from apps.question.models import QuestionMeta
from apps.story.models import Story
from logging import getLogger
logger = getLogger(__name__)


class Command(BaseCommand):
    args = 'question1.url question2.url question3url questiontomergeurl '

    def get_question(self, url):
        path = urlparse.urlparse(url).path
        if not path.startswith('/q/'):
            raise CommandError('%s is not a question url.' % url)
        return QuestionMeta.objects.get(id=base62.to_decimal(path[3:-1]))

    def handle(self, *args, **options):
        if len(args) == 0:
            raise CommandError('You must provide at least 2 question urls.')

        qmeta_urls = list(args)
        target_qmeta = self.get_question(qmeta_urls.pop())

        for qmeta_url in qmeta_urls:
            qmeta_to_merge = self.get_question(qmeta_url)
            Story.objects.filter(question_meta=qmeta_to_merge)\
                         .update(question_meta=target_qmeta)

            qmeta_to_merge.status = QuestionMeta.REDIRECTED
            qmeta_to_merge.redirected_to = target_qmeta
            qmeta_to_merge.save(update_fields=['status', 'redirected_to'])

            logger.info('%s merged to %s' % (qmeta_to_merge, target_qmeta))
