from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext as _
from resmin.libs.baseconv import base62
from redis_cache import get_redis_connection

from utils import (filename_for_image, filename_for_upload, generate_upload_id)

from utils.models import BaseModel, UniqueFileModel
from geoposition.fields import GeopositionField

redis = get_redis_connection('default')


class Story(BaseModel):

    STATUS_CHOICES = (
        (0, 'Published'),
        (1, 'Deleted by Owner'),
        (2, 'Deleted by Admins'))

    VISIBLE_FOR_CHOICES = (
        (0, _('Everyone')),
        (1, _('My Followers')))

    LIKE_SET_PATTERN = 'answer:%s:likes'

    question = models.ForeignKey(
        'question.QuestionMeta', null=True, blank=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(_('Description'), null=True, blank=True)
    is_nsfw = models.BooleanField(_('NSFW'), default=False)
    is_anonymouse = models.BooleanField(_('Hide my name'), default=False)
    like_count = models.PositiveIntegerField(default=0)
    status = models.PositiveSmallIntegerField(default=0,
                                              choices=STATUS_CHOICES)
    visible_for = models.PositiveSmallIntegerField(
        default=0, verbose_name=_('Visible For'),
        choices=VISIBLE_FOR_CHOICES)
    visible_for_users = models.ManyToManyField(
        User, related_name='visible_for_users', null=True, blank=True)

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
                if user.id not in self.owner.follower_user_ids:
                    is_visible = False

            # If answer is visible for spesific users
            elif self.visible_for == 2:

                # user must be in visible_for_users list in answer
                if user not in self.visible_for_users.all():
                    is_visible = False

            # If blocked_user_ids didn't given before compute it
            if blocked_user_ids == []:
                from apps.follow.models import compute_blocked_user_ids_for
                blocked_user_ids = compute_blocked_user_ids_for(user)

            # If answer owner blocked user, or user blocked answer owner
            # Story is not visible.
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
        return self.LIKE_SET_PATTERN % self.id

    def set_like(self, user, liked=True):
        """

        @type liked: object
        """
        from apps.account.models import UserProfile
        from apps.question.signals import story_like_changed

        if liked:
            result = redis.sadd(self._like_set_key(), user.username)
            if result:
                redis.zincrby(
                    UserProfile.scoreboard_key(), self.owner.username, 1)
                story_like_changed.send(sender=self)
        else:
            result = redis.srem(self._like_set_key(), user.username)
            if result:
                redis.zincrby(
                    UserProfile.scoreboard_key(), self.owner.username, -1)
                story_like_changed.send(sender=self)
        return result

    def get_absolute_url(self):
        return reverse('story', kwargs={
            'base62_id': base62.from_decimal(self.id)})

    def get_likers_from_redis(self):
        return [User(username=username) for username in
                redis.smembers(self._like_set_key())]

    def get_like_count_from_redis(self):
        return redis.scard(self._like_set_key())

    def update_like_count(self):
        """Updates self.likes count from redis db, it does not save, must
        be saved manually."""
        self.like_count = self.get_like_count_from_redis()

    def __unicode__(self):
        return self.title if self.title else u'Story by %s' % self.owner

    class Meta:
        ordering = ['-created_at']


class Image(UniqueFileModel):
    UNIQUE_FILE_FIELD = 'image'
    image = models.ImageField(upload_to=filename_for_image)

    def serialize(self):
        return {'url': True}


class Slot(models.Model):
    order = models.PositiveIntegerField()
    story = models.ForeignKey(Story, null=True, blank=True)
    title = models.CharField(max_length=144, null=True, blank=True)
    image = models.ForeignKey(Image)
    description = models.TextField(null=True, blank=True)
    position = GeopositionField(null=True, blank=True)

    def __unicode__(self):
        return u'%s of %s' % (self.order, self.story)

    class Meta:
        unique_together = ('order', 'story')
        ordering = ['story', 'order']


class Upload(models.Model):
    UPLOADING = 1
    COMPLETE = 2
    FAILED = 3

    STATUS_CHOICES = (
        (UPLOADING, _('Uploading')),
        (COMPLETE, _('Complete')),
        (FAILED, _('Failed')),
    )

    MODEL_CHOICES = (
        ('image', Image.__name__),
    )

    MODEL_MAPPING = {
        'image': Image
    }

    owner = models.ForeignKey(User)
    upload_id = models.CharField(max_length=32, unique=True, editable=False,
                                 default=generate_upload_id)
    file = models.FileField(max_length=255, upload_to=filename_for_upload)
    offset = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    model = models.CharField(max_length=64, choices=MODEL_CHOICES)
    completed_at = models.DateTimeField(auto_now_add=True)
    status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES)

    def get_object(self):
        klass = self.MODEL_MAPPING[self.model]
        field = klass.FILE_FIELD
        return klass.objects.get_or_create(**{field: self.file})
