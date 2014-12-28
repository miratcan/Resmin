from django.db import models
from django.contrib.auth.models import User
from apps.story.models import Story
# Create your models here.


class Comment(models.Model):
    story = models.ForeignKey(Story)
    body = models.TextField()
    as_html = models.TextField(blank=True)
    posted_by = models.ForeignKey(User, related_name="posted_by")
    posted_at = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return u"%s's comment on %s" % (self.posted_by, self.story)
