import hashlib
from json import dumps
from datetime import datetime
from sorl.thumbnail import get_thumbnail

from django.contrib.auth.models import User
from django.contrib.contenttypes.generic import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.core.files import File
from django.core.files.base import ContentFile
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext as _
from redis_cache import get_redis_connection

from utils import (filename_for_image, filename_for_upload, generate_upload_id)
from utils.models import BaseModel, UniqueFileModel
from geoposition.fields import GeopositionField

from apps.story.managers import StoryManager

redis = get_redis_connection('default')


class Story(BaseModel):

    DRAFT = 0
    PUBLISHED = 1
    DELETED_BY_OWNER = 2
    DELETED_BY_ADMINS = 3

    VISIBLE_FOR_EVERYONE = 0
    VISIBLE_FOR_FOLLOWERS = 0

    STATUS_CHOICES = ((DRAFT, _('Draft')),
                      (PUBLISHED, _('Published')),
                      (DELETED_BY_OWNER, _('Deleted by Owner')),
                      (DELETED_BY_ADMINS, _('Deleted by Admins')))

    VISIBLE_FOR_CHOICES = ((VISIBLE_FOR_EVERYONE, _('Everyone')),
                           (VISIBLE_FOR_FOLLOWERS, _('Followers')))

    LIKE_SET_PATTERN = 'answer:%s:likes'
    mounted_question_metas = models.ManyToManyField(
        'question.QuestionMeta', null=True, blank=True)
    question = models.ForeignKey('question.Question', null=True, blank=True)
    title = models.CharField(_('Title'), max_length=255, null=True, blank=True)
    description = models.TextField(_('Description'), null=True, blank=True)
    is_nsfw = models.BooleanField(_('NSFW'), default=False)
    is_anonymouse = models.BooleanField(_('Hide my name'), default=False)
    like_count = models.PositiveIntegerField(default=0)
    slot_count = models.PositiveIntegerField(null=True, blank=True)
    status = models.PositiveSmallIntegerField(default=DRAFT,
                                              choices=STATUS_CHOICES)
    visible_for = models.PositiveSmallIntegerField(
        default=VISIBLE_FOR_EVERYONE, verbose_name=_('Visible For'),
        choices=VISIBLE_FOR_CHOICES)
    visible_for_users = models.ManyToManyField(
        User, related_name='visible_for_users', null=True, blank=True)

    objects = StoryManager()

    @property
    def humanized_order(self):
        return self.order + 1

    @property
    def is_deleted(self):
        return bool(self.status)

    def is_liked_by(self, user):
        return redis.sismember(self._like_set_key(), user.username)

    def is_visible_for(self, user, blocked_user_ids=[]):

        if user.is_superuser:
            return True

        is_visible = True
        user_is_authenticated = user.is_authenticated()

        # We don't need to compute user and question owner relationship
        # if user is not authenticated.
        if user_is_authenticated:

            if self.owner == user:
                return True

            # If self is visible for followings
            if self.visible_for == Story.VISIBLE_FOR_FOLLOWERS:

                # user.id must be in owners follower_user_ids
                if user.id not in self.owner.follower_user_ids:
                    is_visible = False

            # If answer is visible for spesific users
            elif self.visible_for == Story.VISIBLE_FOR_USERS:

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
        return is_visible

    def _like_set_key(self):
        return self.LIKE_SET_PATTERN % self.id

    def set_like(self, user, liked=True):
        """
        @type liked: object
        """
        from apps.account.models import UserProfile
        from apps.question.signals import story_like_changed

        is_liked = False

        if liked:
            result = redis.sadd(self._like_set_key(), user.username)
            if result:
                redis.zincrby(
                    UserProfile.scoreboard_key(), self.owner.username, 1)
                story_like_changed.send(sender=self)
                is_liked = True
        else:
            result = redis.srem(self._like_set_key(), user.username)
            if result:
                redis.zincrby(
                    UserProfile.scoreboard_key(), self.owner.username, -1)
                story_like_changed.send(sender=self)
            else:
                is_liked = True
        return is_liked

    def get_absolute_url(self):
        return reverse('story', kwargs={
            'base62_id': self.base62_id})

    def get_update_images_url(self):
        return reverse('update-images-of-story', kwargs={
            'base62_id': self.base62_id})

    def get_update_details_url(self):
        return reverse('update-details-of-story', kwargs={
            'base62_id': self.base62_id})

    def get_likers_from_redis(self):
        return [User(username=username) for username in
                redis.smembers(self._like_set_key())]

    def get_like_count_from_redis(self):
        return redis.scard(self._like_set_key())

    def update_like_count(self):
        """Update self.likes count from redis db, it does not save, must
        be saved manually."""
        self.like_count = self.get_like_count_from_redis()

    def update_slot_count(self):
        self.slot_count = self.slot_set.count()

    def serialize_slots(self):
        data = []
        for slot in self.slot_set.all():  # TODO: Optimise that query.
            data.append({'pk': slot.pk,
                         'order': slot.order,
                         'cPk': slot.cPk,
                         'cTp': 'image',
                         'thumbnailUrl': slot.content.thumbnail_url,
                         'fileCompleted': True})
        return dumps(data)

    def __unicode__(self):
        return self.title if self.title else u'Story by %s' % self.owner

    class Meta:
        ordering = ['-created_at']


class Image(UniqueFileModel):
    UNIQUE_FILE_FIELD = 'image'
    image = models.ImageField(upload_to=filename_for_image)
    taken_at = models.DateTimeField(null=True, blank=True)
    """position = GeopositionField(null=True, blank=True)"""

    @property
    def thumbnail_url(self):
        return get_thumbnail(self.image, '100x100', crop='center').url

    def serialize(self):
        return {'pk': self.pk,
                'thumbnail_url': self.thumbnail_url,
                'small_image_url': get_thumbnail(self.image, '220').url}


class Slot(models.Model):

    order = models.PositiveIntegerField(null=True)
    story = models.ForeignKey(Story, null=True, blank=True)
    title = models.CharField(max_length=144, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    cPk = models.PositiveIntegerField()
    cTp = models.ForeignKey(ContentType)

    content = GenericForeignKey('cTp', 'cPk')
    created_at = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return u'%s of %s' % (self.order, self.story)

    class Meta:
        ordering = ['story', 'order']


class UploadError(Exception):
    def __init__(self, status, **data):
        self.status = status
        self.data = data


class Upload(models.Model):

    UPLOADING = 1
    COMPLETE = 2
    FAILED = 3

    STATUS_CHOICES = ((UPLOADING, _('Uploading')),
                      (COMPLETE, _('Complete')),
                      (FAILED, _('Failed')))

    MODEL_CHOICES = (('image', Image.__name__),)
    MODEL_MAPPING = {'image': Image}

    owner = models.ForeignKey(User)
    upload_id = models.CharField(max_length=32, unique=True, editable=False,
                                 default=generate_upload_id)
    file = models.FileField(max_length=255, upload_to=filename_for_upload)
    offset = models.PositiveIntegerField(default=0)
    size = models.PositiveIntegerField()
    md5sum = models.CharField(max_length=36, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True)
    completed_at = models.DateTimeField(auto_now_add=True)
    model = models.CharField(max_length=64, choices=MODEL_CHOICES)
    status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES,
                                              default=UPLOADING)

    @property
    def is_completed(self):
        return self.file.size == self.size if self.file else False

    @property
    def file_md5sum(self):
        if not self.file.file.mode == 'rb':
            self.close_file()
        self.file.open()
        md5 = hashlib.md5()
        for chunk in self.file.chunks():
            md5.update(chunk)
        self.close_file()
        return md5.hexdigest()

    def delete_file(self, *args, **kwargs):
        storage, path = self.file.storage, self.file.path
        super(Upload, self).delete(*args, **kwargs)
        storage.delete(path)

    def close_file(self):
        obj = self
        while hasattr(obj, 'file'):
            obj = getattr(obj, 'file')
            obj.close()

    def convert_to_model(self, delete=True):
        """
        Creates model instance that described in model field and deletes this.
        You can override deleting behaviour via delete parameter. If it's
        False Upload object will be kept.
        """

        if not self.status == self.COMPLETE or self.pk is None:
            return None

        model = self.MODEL_MAPPING[self.model]
        obj = model.objects.get_or_create(
            md5sum=self.md5sum,
            defaults={
                model.FILE_FIELD: File(open(self.file.path, 'r'))
            })[0]
        if delete:
            self.delete_file()
            if self.pk is not None:
                self.delete()
        return obj

    def append_data(self, data, size=None, save=True):
        """
        Appends data to file, increases offset with pre calculated size or
        length of data.
        """
        self.close_file()
        self.file.open(mode='ab')
        self.file.write(data)
        self.close_file()
        self.offset += size or (len(data) - 1)

        if self.offset > self.size:
            self.status = self.FAILED
            raise UploadError('Expected file size exceeded.')

        if save:
            self.save()

    def append_chunk(self, chunk, size=None, save=True):
        """
        Appends chunk to file, increases offset with pre calculated size or
        chunk size.
        """
        self.append_data(chunk.read(), size or chunk.get('size'), save=save)

    def save(self, *args, **kwargs):

        if not self.pk:
            if self.size > settings.MAXIMUM_UPLOAD_SIZE:
                raise UploadError('File is too big to upload.')
            self.created_at = datetime.now()
            self.expires_at = self.created_at + \
                settings.UPLOAD_EXPIRATION_TIMEDELTA
            self.file.save(name='', content=ContentFile(''), save=False)

        if self.is_completed:
            if self.file_md5sum == self.md5sum:
                self.status = self.COMPLETE
                self.completed_at = datetime.now()
            else:
                self.status = self.FAILED

        super(Upload, self).save(*args, **kwargs)
