import hashlib

from django.db import models
from django.contrib.auth.models import User, AnonymousUser

from resmin.libs.baseconv import base62


class BaseModel(models.Model):
    owner = models.ForeignKey(User)
    created_at = models.DateTimeField(auto_now_add=True)

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

    class Meta:
        abstract = True
