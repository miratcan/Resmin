from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext as _

from datetime import datetime

from libs.baseconv import base62

from apps.story.models import Story
from apps.follow.models import QuestionFollow


class QuestionMeta(models.Model):

    PUBLISHED = 0
    DELETED_BY_OWNER = 1
    DELETED_BY_ADMINS = 2

    STATUS_CHOICES = ((PUBLISHED, 'Published '),
                      (DELETED_BY_OWNER, 'Deleted by Owner'),
                      (DELETED_BY_ADMINS, 'Deleted by Admins'))

    owner = models.ForeignKey(User, null=True, blank=True)
    text = models.CharField(_('Question'), max_length=512)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    is_featured = models.BooleanField(default=False)
    is_sponsored = models.BooleanField(default=False)
    answer_count = models.PositiveIntegerField(default=0)
    follower_count = models.PositiveIntegerField(default=0)
    status = models.PositiveSmallIntegerField(default=0,
                                              choices=STATUS_CHOICES)
    cover_answer = models.ForeignKey(
        'story.Story', related_name='cover_answer', null=True, blank=True)
    latest_answer = models.ForeignKey(
        'story.Story', related_name='latest_answer', null=True, blank=True)

    class Meta:
        ordering = ["-is_featured", "-updated_at"]

    def __unicode__(self):
        return self.text

    @property
    def cover_image(self):
        if not self.cover_answer:
            answers = self.answer_set\
                .filter(status=0, is_nsfw=False)\
                .order_by('-like_count')
            if answers:
                self.cover_answer = answers[0]
                self.save()
        return self.cover_answer.image

    @property
    def is_deleted(self):
        return bool(self.status)

    def is_deletable_by(self, user, answers=None):
        answers = self.answer_set.filter(status=0) if answers is \
            None else answers
        if settings.ONLY_QUESTIONS_WITHOUT_ANSWERS_CAN_BE_DELETED:
            answer_count = len(answers)
        else:
            answer_count = 0

        return True if user.is_authenticated() and not self.is_deleted \
                       and answer_count == 0 else False

    @property
    def base62_id(self):
        return base62.from_decimal(self.id)

    def get_absolute_url(self):
        return reverse('question', kwargs={
            'base62_id': base62.from_decimal(self.id)})

    def get_deletion_url(self):
        return reverse('delete_question', kwargs={
            'base62_id': base62.from_decimal(self.id)})

    def update_answer_count(self):
        """Updates answer_count but does not saves question
        instance, it have to be saved later."""
        self.answer_count = self.story_set.filter(
            status=Story.PUBLISHED).count()

    def update_follower_count(self):
        """
        Update follower_count but does not saves question.
        """
        self.follower_count = self.follow_set.filter(
            status=QuestionFollow.FOLLOWING).count()

    def update_updated_at(self):
        self.updated_at = datetime.now()


class Question(models.Model):

    PENDING = 0
    ANSWERED = 1
    REJECTED = 2

    questioner = models.ForeignKey(User, null=True, blank=True,
                                   related_name='questioner')
    meta = models.ForeignKey(QuestionMeta)
    questionee = models.ForeignKey(User, related_name='questionee')
    is_anonymouse = models.BooleanField(default=False)
    answer = models.ForeignKey('story.Story', related_name='answer',
                               null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.PositiveSmallIntegerField(
        default=0, choices=((PENDING, 'Pending'),
                            (ANSWERED, 'Answered'),
                            (REJECTED, 'Rejected')))

    def __unicode__(self):
        return '%s - %s -> %s' % (self.questioner, self.meta.text,
                                  self.questionee)

    def post_answer_url(self):
        return '%s?qid=%s' % (
            reverse('create-story', kwargs={
                'base62_id': self.meta.base62_id}), self.id)
