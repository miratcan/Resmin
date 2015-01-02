from django.db import models
from django.contrib.auth.models import User
from apps.story.models import Story
# Create your models here.


class Comment(models.Model):

    PUBLISHED = 1
    DELETED_BY_OWNER = 2
    DELETED_BY_STORY_OWNER = 3
    DELETED_BY_ADMINS = 4
    STATUS_CHOICES = ((PUBLISHED, 'Published'),
                      (DELETED_BY_OWNER, 'Deleted by owner'),
                      (DELETED_BY_STORY_OWNER, 'Deleted by story owner'),
                      (DELETED_BY_ADMINS, 'Deleted by story owner'))

    story = models.ForeignKey(Story)
    body = models.TextField()
    as_html = models.TextField(blank=True)
    posted_by = models.ForeignKey(User, related_name="posted_by")
    posted_at = models.DateTimeField(auto_now_add=True)
    status = models.PositiveSmallIntegerField(STATUS_CHOICES)

    def __unicode__(self):
        return u"%s's comment on %s" % (self.posted_by, self.story)
