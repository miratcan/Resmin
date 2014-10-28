from django.db import models
from django.db.models import Sum
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.dispatch import receiver
from utils.models import BaseModel
from apps.follow.models import UserFollow

from libs import key_generator
from utils import unique_filename_for_avatar


class UserProfile(models.Model):
    user = models.OneToOneField(User)
    bio = models.CharField(_('bio'), max_length=255, null=True, blank=True)
    website = models.URLField(_('website'), null=True, blank=True)
    like_count = models.PositiveIntegerField(default=0)
    follower_count = models.PositiveIntegerField(default=0)
    following_count = models.PositiveIntegerField(default=0)
    answer_count = models.PositiveIntegerField(default=0)
    location = models.CharField(_('location'), max_length=64,
                                null=True, blank=True)

    avatar = models.ImageField(upload_to=unique_filename_for_avatar,
                               null=True,
                               blank=True)

    @staticmethod
    def scoreboard_key():
        return 'like_scoreboard'

    def update_like_count(self):
        self.like_count = self.user.answer_set.filter(status=0)\
            .aggregate(like_count_total=Sum('like_count'))['like_count_total']\
            or 0

    def update_follower_count(self):
        self.follower_count = UserFollow.objects.filter(
            target=self.user, status=1).count()

    def update_following_count(self):
        self.following_count = UserFollow.objects.filter(
            follower=self.user, status=1).count()

    def update_answer_count(self):
        self.answer_count = self.user.answer_set.filter(status=0).count()

    def __unicode__(self):
        return "%s's profile" % self.user

    def get_absolute_url(self):
        reverse('profile', args=[self.user.username, ])

# TODO: Remove it.
User.profile = property(
    lambda u: UserProfile.objects.get_or_create(user=u)[0])


class Invitation(models.Model):
    owner = models.ForeignKey(User, null=True, blank=True)
    key = models.CharField(max_length=255, blank=True)
    used_by = models.ForeignKey(User, null=True, blank=True,
                                related_name='used_by')

    def get_absolute_url(self):
        return reverse('register') + "?key=%s" % self.key

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = key_generator()
        super(Invitation, self).save(*args, **kwargs)


class EmailCandidate(BaseModel):
    email = models.EmailField(_('email'))
    key = models.CharField(max_length=255, blank=True)

    def save(self, *args, **kwargs):
        self.key = key_generator(size=10)
        super(EmailCandidate, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('email_confirm', kwargs={'key': self.key})


@receiver(post_save, sender=User)
def user_created_callback(sender, **kwargs):
    if kwargs.get('created'):
        UserProfile.objects.get_or_create(user=kwargs['instance'])
