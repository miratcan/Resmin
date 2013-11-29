from django.contrib.auth.models import User, AnonymousUser
from django.core.urlresolvers import reverse
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext as _

from datetime import datetime
from redis_cache import get_redis_connection

from utils import unique_filename_for_answer
from libs.baseconv import base62


redis = get_redis_connection('default')


class BaseModel(models.Model):
    owner = models.ForeignKey(User)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_owner(self):
        if hasattr(self, 'is_anonymouse'):
            return AnonymousUser if self.is_anonymouse else self.owner
        else:
            return self.owner

    def base62_id(self):
        return base62.from_decimal(self.id)

    class Meta:
        abstract = True


class Question(BaseModel):
    text = models.CharField(_('Question'), max_length=512)
    is_anonymouse = models.BooleanField(_('Hide my name'), default=False)
    is_featured = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now_add=True)
    merged_to = models.ForeignKey(
        'self', null=True, blank=True, related_name='m_to')
    answer_count = models.PositiveIntegerField(default=0)
    status = models.PositiveSmallIntegerField(
        default=0, choices=((0, 'Published '),
                            (1, 'Deleted by Owner'),
                            (2, 'Deleted by Admins')))

    class Meta:
        ordering = ["-is_featured", "-updated_at"]

    def __unicode__(self):
        return unicode(self.text)

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

    def get_absolute_url(self):
        return reverse('question', kwargs={
            'base62_id': base62.from_decimal(self.id)})

    def get_deletion_url(self):
        return reverse('delete_question', kwargs={
            'base62_id': base62.from_decimal(self.id)})

    def update_answer_count(self):
        """Updates answer_count but does not saves question
        instance, it have to be saved later."""
        self.answer_count = self.answer_set.filter(status=0).count()

    def update_updated_at(self):
        self.updated_at = datetime.now()


class Answer(BaseModel):
    question = models.ForeignKey(Question)
    image = models.ImageField(upload_to=unique_filename_for_answer)
    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    source_url = models.URLField(null=True, blank=True)
    is_nsfw = models.BooleanField(_('NSFW'), default=False)
    is_anonymouse = models.BooleanField(_('Hide my name'), default=False)
    like_count = models.PositiveIntegerField(default=0)
    status = models.PositiveSmallIntegerField(
        default=0,
        choices=((0, 'Published'),
                 (1, 'Deleted by Owner'),
                 (2, 'Deleted by Admins')))
    visible_for = models.PositiveSmallIntegerField(
        verbose_name=_('Visible For'),
        choices=((0, _('Everyone')),
                 (1, _('My Followers'))))
    visible_for_users = models.ManyToManyField(
        User, related_name='visible_for_users', null=True, blank=True)
    LIKES_SET_PATTERN = 'answer:%s:likes'

    @property
    def is_deleted(self):
        return bool(self.status)

    def is_liked_by(self, user):
        return redis.sismember(self._like_set_key(), user.username)

    def is_visible_for(self, user, blocked_user_ids=[]):
        is_visible = True
        user_is_authenticated = user.is_authenticated()

        # We don't need to compute user and question owner relationship
        # if user is not authenticated.
        if user_is_authenticated:

            if self.owner == user:
                return True

            # If self is visible for followings
            if self.visible_for == 1:

                # user.id must be in owners follower_user_ids
                if not user.id in self.owner.follower_user_ids:
                    is_visible = False

            # If answer is visible for spesific users
            elif self.visible_for == 2:

                # user must be in visible_for_users list in answer
                if not user in self.visible_for_users.all():
                    is_visible = False

            # If blocked_user_ids didn't given before compute it
            if blocked_user_ids == []:
                from apps.follow.models import compute_blocked_user_ids_for
                blocked_user_ids = compute_blocked_user_ids_for(user)

            # If answer owner blocked user, or user blocked answer owner
            # Answer is not visible.
            if self.owner_id in blocked_user_ids or \
               user.id in blocked_user_ids:
                is_visible = False
        else:
            # If user is not authenticated and visible_for=0 we can
            # display it.
            if self.visible_for in (1, 2):
                is_visible = False
        return is_visible


    def _like_set_key(self):
        return self.LIKES_SET_PATTERN % self.id

    def set_like(self, user, liked=True):
        from apps.account.models import UserProfile
        from apps.question.signals import answer_like_changed

        if liked:
            result = redis.sadd(self._like_set_key(), user.username)
            if result:
                redis.zincrby(
                    UserProfile.scoreboard_key(), self.owner.username, 1)
                answer_like_changed.send(sender=self)
        else:
            result = redis.srem(self._like_set_key(), user.username)
            if result:
                redis.zincrby(
                    UserProfile.scoreboard_key(), self.owner.username, -1)
                answer_like_changed.send(sender=self)
        return result

    def get_absolute_url(self):
        return reverse('answer', kwargs={
            'base62_id': base62.from_decimal(self.id)})

    def get_likers_from_redis(self):
        for username in redis.smembers(self._like_set_key()):
            yield User(username=username)

    def get_like_count_from_redis(self):
        return redis.scard(self._like_set_key())

    def update_like_count(self):
        """Updates self.likes count from redis db, it does not save, must
        be saved manually."""
        self.like_count = self.get_like_count_from_redis()

    class Meta:
        ordering = ['-created_at']
