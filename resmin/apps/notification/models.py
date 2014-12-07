from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericForeignKey


class NotificationType(models.Model):
    slug = models.SlugField(max_length=255)
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name


class NotificationPreference(models.Model):

    SHOW_ON_SITE = 0
    SENT_ME_EMAIL = 1

    user = models.ForeignKey(User)
    ntype = models.ForeignKey(NotificationType)
    subscription_status = models.PositiveIntegerField(choices=(
        (SHOW_ON_SITE, "Only show on site"),
        (SENT_ME_EMAIL, "Send me email")), default=0)

    def __unicode__(self):
        return '%s\'s setting on %s notifications' % (
            self.user, self.ntype)


class Notification(models.Model):
    actor = models.ForeignKey(
        User, related_name='actor', null=True, blank=True)
    recipient = models.ForeignKey(
        User, related_name='recipient', null=True, blank=True)
    target_ct = models.ForeignKey(
        ContentType, blank=True, null=True)
    target_oid = models.PositiveIntegerField(blank=True, null=True)
    target = GenericForeignKey('target_ct', 'target_oid')
    url = models.CharField(max_length=255)
    ntype = models.ForeignKey(NotificationType)
    date = models.DateTimeField(auto_now_add=True)
    custom_message = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "notifications"

    def __unicode__(self):
        return "'%s' notification for %s" % (self.ntype, self.recipient)
