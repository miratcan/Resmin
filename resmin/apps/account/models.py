
from django.db import models
from django.db.models import Sum
from django.db.models.signals import post_save
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.dispatch import receiver

from resmin.utils.models import BaseModel
from resmin.utils import filename_for_avatar

from libs import key_generator


class UserProfile(models.Model):
    user = models.OneToOneField(User)
    bio = models.CharField(_('bio'), max_length=255, null=True, blank=True)
    website = models.URLField(_('website'), null=True, blank=True)
    facebook = models.SlugField(_('facebook username'), null=True, blank=True)
    instagram = models.SlugField(_('instagram username'), null=True, blank=True)
    twitter = models.SlugField(_('twitter username'), null=True, blank=True)
    github = models.SlugField(_('github username'), null=True, blank=True)
    like_count = models.PositiveIntegerField(default=0)
    follower_count = models.PositiveIntegerField(default=0)
    following_count = models.PositiveIntegerField(default=0)
    story_count = models.PositiveIntegerField(default=0)
    location = models.CharField(_('location'), max_length=64,
                                null=True, blank=True)

    avatar = models.ImageField(upload_to=filename_for_avatar, null=True,
                               blank=True)

    @staticmethod
    def scoreboard_key():
        return 'like_scoreboard'

    def update_like_count(self):
        from apps.story.models import Story
        self.like_count = self.user.story_set.filter(status=Story.PUBLISHED)\
            .aggregate(like_count_total=Sum('like_count'))['like_count_total']\
            or 0

    def update_follower_count(self):
        from apps.follow.models import UserFollow
        self.follower_count = UserFollow.objects.filter(
            target=self.user).count()

    def update_following_count(self):
        from apps.follow.models import UserFollow
        self.following_count = UserFollow.objects.filter(
            follower=self.user).count()

    def update_story_count(self):
        from apps.story.models import Story
        self.story_count = self.user.story_set.filter(
            status=Story.PUBLISHED).count()

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
    used_count = models.PositiveIntegerField(default=0)
    use_limit = models.PositiveIntegerField(
        default=settings.DEFAULT_INVITATION_USE_LIMIT)
    registered_users = models.ManyToManyField(User, null=True, blank=True,
                                              related_name='registed_users')
    is_usable = models.BooleanField(default=True)

    @property
    def remaining_use(self):
        return self.use_limit - self.used_count

    def get_absolute_url(self):
        return reverse('register') + "?key=%s" % self.key

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = key_generator()
        if self.pk is not None:
            self.used_count = self.registered_users.count()
        return super(Invitation, self).save(*args, **kwargs)

    class Meta:
        ordering = ['is_usable']


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
