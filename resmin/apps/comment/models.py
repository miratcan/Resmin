from django.db import models
from django.contrib.auth.models import User
from apps.story.models import Story
from django.template.defaultfilters import linebreaks, urlize


class CommentManager(models.Manager):
    def published(self):
        return self.get_queryset().filter(status=Comment.PUBLISHED)

COMMENT_RENDERER = lambda b: linebreaks(urlize(b))


class Comment(models.Model):

    PUBLISHED = 1
    DELETED_BY_OWNER = 2
    DELETED_BY_STORY_OWNER = 3
    DELETED_BY_ADMINS = 4
    STATUS_CHOICES = ((PUBLISHED, 'Published'),
                      (DELETED_BY_OWNER, 'Deleted by owner'),
                      (DELETED_BY_STORY_OWNER, 'Deleted by story owner'),
                      (DELETED_BY_ADMINS, 'Deleted by admins'))

    story = models.ForeignKey(Story)
    body = models.TextField()
    as_html = models.TextField(blank=True)
    owner = models.ForeignKey(User)
    posted_at = models.DateTimeField(auto_now_add=True)
    status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES)
    objects = CommentManager()

    def __unicode__(self):
        return u"%s's comment on %s" % (self.owner, self.story)

    def get_absolute_url(self):
        return '%s#c%s' % (self.story.get_absolute_url(), self.id)

    def save(self, *args, **kwargs):
        self.as_html = COMMENT_RENDERER(self.body)
        super(Comment, self).save(*args, **kwargs)
