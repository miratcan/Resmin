import hashlib
from sorl.thumbnail import get_thumbnail

from django.db import models
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext as _

from resmin.libs.baseconv import base62


class BaseModel(models.Model):
    owner = models.ForeignKey(User, verbose_name=_('Owner'))
    created_at = models.DateTimeField(auto_now_add=True,
                                      verbose_name=_('Created at'))

    def get_owner(self):
        if hasattr(self, 'is_anonymouse'):
            return AnonymousUser if self.is_anonymouse else self.owner
        else:
            return self.owner

    @property
    def base62_id(self):
        return base62.from_decimal(self.id)

    class Meta:
        abstract = True


class UniqueFileModel(models.Model):
    """
    TODO: add unique=True property to given file field when initializing.
    """

    FILE_FIELD = 'image'
    md5sum = models.CharField(max_length=36, blank=True)

    def _update_md5sum(self):
        md5 = hashlib.md5()
        for chunk in getattr(self, self.FILE_FIELD).chunks():
            md5.update(chunk)
        self.md5sum = md5.hexdigest()

    @property
    def thumbnail_url(self, size='100x100'):
        return get_thumbnail(self.image, size, crop='center').url

    def serialize(self):
        return {'cPk': self.pk,
                'cTp': ContentType.objects.get_for_model(self).pk,
                'thumbnail_url': self.thumbnail_url}

    class Meta:
        abstract = True
