from django.contrib.auth.models import User

from django.db import models
from django.db.models.query import QuerySet

from ..story.models import Story
from ..follow.models import compute_blocked_user_ids_for

from django.template.defaultfilters import linebreaks, urlize


class CommentQuerySet(QuerySet):

    def from_active_owners(self):
        return self.filter(owner__is_active=True)

    def published(self):
        return self.filter(status=Comment.PUBLISHED)

    def visible_for(self, user, blocked_user_ids=None):
        if not blocked_user_ids:
            blocked_user_ids = compute_blocked_user_ids_for(user)
        return self.exclude(owner_id__in=blocked_user_ids)


class CommentManager(models.Manager):

    def get_query_set(self):
        return CommentQuerySet(self.model)

    def from_active_owners(self):
        return self.get_queryset().from_active_owners()

    def published(self):
        return self.get_queryset().published()

    def visible_for(self, user, blocked_user_ids=None):
        return self.get_queryset().visible_for(user, blocked_user_ids)


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
