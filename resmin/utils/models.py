from django.db import models
from django.contrib.auth.models import User, AnonymousUser


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
