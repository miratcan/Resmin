import magic
import hashlib

from logging import getLogger
from json import dumps
from datetime import datetime
from sorl.thumbnail import get_thumbnail
from jsonfield import JSONField

from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.core.files import File
from django.core.files.base import ContentFile
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext as _
from django_redis import get_redis_connection

from resmin.utils import (filename_for_image, filename_for_upload,
                          generate_upload_id, filename_for_video,
                          filename_for_video_frame)
from resmin.utils.models import BaseModel, UniqueFileModel
from ..follow.models import compute_blocked_user_ids_for
from ..account.models import UserProfile
from ..question.signals import story_like_changed

from .managers import StoryManager
from .video_processing import grab_frame

redis = get_redis_connection('default')
logger = getLogger(__name__)


class Story(BaseModel):

    DRAFT = 0
    PUBLISHED = 1
    DELETED_BY_OWNER = 2
    DELETED_BY_ADMINS = 3

    STATUS_CHOICES = ((DRAFT, _('Draft')),
                      (PUBLISHED, _('Published')),
                      (DELETED_BY_OWNER, _('Deleted by Owner')),
                      (DELETED_BY_ADMINS, _('Deleted by Admins')))

    LIKE_SET_PATTERN = 'answer:%s:likes'
    question = models.ForeignKey('question.Question', null=True, blank=True)
    question_meta = models.ForeignKey('question.QuestionMeta')
    title = models.CharField(_('Title'), max_length=255, null=True, blank=True)
    cover_img = JSONField(_('Cover Image'), null=True, blank=True)
    description = models.TextField(_('Description'), null=True, blank=True)
    is_featured = models.BooleanField(_('Featured'), default=False)
    is_nsfw = models.BooleanField(_('NSFW'), default=False)
    is_anonymouse = models.BooleanField(_('Hide my name'), default=False)
    is_playble = models.BooleanField(default=False)
    like_count = models.PositiveIntegerField(default=0)
    slot_count = models.PositiveIntegerField(null=True, blank=True)
    comment_count = models.PositiveIntegerField(null=True, blank=True)
    status = models.PositiveSmallIntegerField(
        _('Status'), default=DRAFT,
        choices=STATUS_CHOICES)
    updated_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Updated at'))

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

        if user.is_authenticated():

            if self.owner_id == user.id:
                return True

            if blocked_user_ids == []:
                blocked_user_ids = compute_blocked_user_ids_for(user)

            if self.owner_id in blocked_user_ids or \
               user.id in blocked_user_ids:
                return False

        if self.status == Story.PUBLISHED:
            return True

        return False

    def _like_set_key(self):
        return self.LIKE_SET_PATTERN % self.id

    def set_like(self, user, liked=True):
        """
        @type liked: object
        """

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

    def get_slot_count(self):
        if not self.slot_count:
            self.slot_count = self.slot_set.all().count()
            self.save(update_fields=['slot_count'])
        return self.slot_count

    def get_cover_img(self):
        if not self.cover_img:
            try:
                slot = self.slot_set.first()
                thmb = get_thumbnail(slot.content.image, '220')
                self.cover_img = {'url': thmb.url,
                                  'width': thmb.width,
                                  'height': thmb.height}
                self.save(update_fields=['cover_img'])
            except:
                logger.error('Could\'nt generate cover image '
                             'for Story: %s' % self.id)
        return self.cover_img

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

    def get_next_story(self, requested_user=None):
        blocked_user_ids = compute_blocked_user_ids_for(requested_user) if \
            requested_user else []
        return Story.objects.filter(
            question_meta=self.question_meta,
            status=Story.PUBLISHED,
            created_at__lt=self.created_at)\
            .exclude(owner_id__in=blocked_user_ids)\
            .order_by('-created_at').first()

    def get_prev_story(self, requested_user=None):
        blocked_user_ids = compute_blocked_user_ids_for(requested_user) \
            if requested_user else []
        return Story.objects.filter(
            question_meta=self.question_meta,
            status=Story.PUBLISHED,
            created_at__gt=self.created_at)\
            .exclude(owner_id__in=blocked_user_ids)\
            .order_by('created_at').first()

    def update_like_count(self, save=False):
        """Update self.likes count from redis db, it does not save, must
        be saved manually."""
        self.like_count = self.get_like_count_from_redis()
        if save:
            self.save(update_fields=['like_count'])

    def update_slot_count(self, save=False):
        self.slot_count = self.slot_set.count()
        if save:
            self.save(update_fields=['slot_count'])

    def update_comment_count(self, save=False):
        from apps.comment.models import Comment
        self.comment_count = Comment.objects.filter(
            status=Comment.PUBLISHED, story=self).count()
        if save:
            self.save(update_fields=['comment_count'])

    def set_updated_at_to_now(self, save=False):
        self.updated_at = datetime.now()
        if save:
            self.save(update_fields=['updated_at'])

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
        verbose_name = _('Story')
        verbose_name_plural = _('Stories')


class Video(UniqueFileModel):
    FILE_FIELD = 'video'
    video = models.FileField(upload_to=filename_for_video)
    frame = models.ImageField(upload_to=filename_for_video_frame, blank=True)
    taken_at = models.DateTimeField(null=True, blank=True)
    mime_type = models.CharField(max_length=64)

    @property
    def image(self):
        if not self.frame:
            img_path = grab_frame(self.video.path)
            if img_path:
                self.frame = File(open(img_path, 'r'))
                self.save()
            else:
                return None
        return self.frame

    class Meta:
        verbose_name = _('Video')
        verbose_name_plural = _('Videos')


class Image(UniqueFileModel):
    FILE_FIELD = 'image'
    image = models.ImageField(upload_to=filename_for_image)
    taken_at = models.DateTimeField(null=True, blank=True)
    mime_type = models.CharField(max_length=64)
    is_playble = models.BooleanField(blank=True)

    def save(self, *args, **kwargs):
        self.is_playble = self.mime_type in settings.PLAYBLE_MIME_TYPES
        super(Image, self).save(*args, **kwargs)

    class Meta:
        verbose_name = _('Image')
        verbose_name_plural = _('Images')


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
        verbose_name = _('Slot')
        verbose_name_plural = _('Slots')


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

    MODEL_CHOICES = (('image', Image.__name__),
                     ('video', Video.__name__))

    MIME_MAPPING = {'image/png': Image,
                    'image/jpeg': Image,
                    'image/gif': Image,
                    'video/webm': Video,
                    'video/mp4': Video}

    owner = models.ForeignKey(User, verbose_name=_('Owner'))
    upload_id = models.CharField(max_length=32, unique=True, editable=False,
                                 default=generate_upload_id)
    file = models.FileField(max_length=255, upload_to=filename_for_upload)
    mime_type = models.CharField(max_length=64)
    offset = models.PositiveIntegerField(default=0)
    size = models.PositiveIntegerField()
    md5sum = models.CharField(max_length=36, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True)
    completed_at = models.DateTimeField(auto_now_add=True)
    model = models.CharField(max_length=64, blank=True, choices=MODEL_CHOICES)
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

        model = self.MIME_MAPPING[self.mime_type]
        obj = model.objects.get_or_create(
            md5sum=self.md5sum,
            defaults={
                model.FILE_FIELD: File(open(self.file.path, 'r')),
                'mime_type': self.mime_type
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
        if self.offset == 0:
            self.mime_type = magic.from_buffer(data, mime=True)
            try:
                self.model = self.MIME_MAPPING[
                    self.mime_type].__name__.lower()
            except KeyError:
                raise UploadError('Mime type is not supported.')

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

    class Meta:
        verbose_name = _('Upload')
        verbose_name_plural = _('Uploads')
