from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.db import models

from libs import key_generator


class FollowBase(models.Model):
    follower = models.ForeignKey(User)

    class Meta:
        abstract = True


class QuestionFollow(FollowBase):

    FOLLOWING = 0
    UNFOLLOWED = 1

    ASKED = 0
    ANSWERED = 1
    FOLLOWED = 2

    STATUS_CHOICES = ((FOLLOWING, 'Following'),
                      (UNFOLLOWED, 'Unfollowed'))

    REASON_CHOICES = ((ASKED, 'Asked'),
                      (ANSWERED, 'Answered'),
                      (FOLLOWED, 'Followed'))

    target = models.ForeignKey('question.QuestionMeta',
                               related_name='follow_set')
    status = models.PositiveSmallIntegerField(default=0,
                                              choices=STATUS_CHOICES)
    key = models.CharField(max_length=255, blank=True)
    reason = models.PositiveIntegerField(max_length=16, choices=REASON_CHOICES)

    def __unicode__(self):
        return '%s %s %s' % (self.follower, self.reason, self.target)

    def save(self, *args, **kwargs):
        self.key = key_generator(size=10)
        super(QuestionFollow, self).save(*args, **kwargs)

    def cancellation_url(self):
        return reverse('cancel_follow', kwargs={'key': self.key})


class StoryFollow(FollowBase):

    REASON_CREATED = 'created'
    REASON_COMMENTED = 'commented'

    target = models.ForeignKey('story.Story', related_name='target')
    status = models.PositiveSmallIntegerField(
        default=0, choices=((0, 'Following'),
                            (1, 'Unfollowed')))
    key = models.CharField(max_length=255, blank=True)
    reason = models.CharField(max_length=16,
                              choices=((REASON_CREATED, 'Created'),
                                       (REASON_COMMENTED, 'Commented')))


class UserFollow(FollowBase):

    PENDING = 0
    FOLLOWING = 1
    BLOCKED = 2
    FOLLOWING_RESTRICTED = 3

    target = models.ForeignKey(User, related_name='user')
    status = models.PositiveSmallIntegerField(
        default=0, choices=((PENDING, 'Pending'),
                            (FOLLOWING, 'Following'),
                            (FOLLOWING_RESTRICTED, 'Following as Restricted'),
                            (BLOCKED, 'Blocked')))

    def __unicode__(self):
        return '%s %s %s' % (self.follower,
                             self.get_status_display().lower(),
                             self.target)

FOLLOWING_STATUSES = [UserFollow.FOLLOWING, UserFollow.FOLLOWING_RESTRICTED]

User.is_blocked = lambda u, t: bool(
    UserFollow.objects.filter(
        follower=u, target=t, status=UserFollow.BLOCKED).exists())

User.is_blocked_by = lambda u, t: bool(
    UserFollow.objects.filter(
        follower=t, target=u, status=UserFollow.BLOCKED).exists())

User.is_following = lambda u, t: UserFollow.objects.filter(
    follower=u, target=t, status__in=FOLLOWING_STATUSES).exists()

User.has_pending_follow_request = lambda u, t: \
    UserFollow.objects.filter(follower=u, target=t,
                              status=UserFollow.PENDING).exists()

# Return all follower user ids.
User.follower_user_ids = \
    property(lambda u: [f.follower_id for f in UserFollow.objects.filter(
             target=u, status__in=FOLLOWING_STATUSES)])

# Return unrestricted follower user ids.
User.follower_unrestricted_user_ids = \
    property(lambda u: [f.follower_id for f in UserFollow.objects.filter(
             target=u, status=UserFollow.FOLLOWING)])

# Return all following user ids.
User.following_user_ids = \
    property(lambda u: [f.target_id for f in UserFollow.objects.filter(
             follower=u, status__in=FOLLOWING_STATUSES,
             target__is_active=True)])

# Return all follower user ids.
User.following_unrestricted_user_ids = \
    property(lambda u: [f.target_id for f in UserFollow.objects.filter(
             follower=u, status=UserFollow.FOLLOWING,
             target__is_active=True)])

# Return unrestricted follower user ids.
User.follower_users = \
    property(lambda u: [f.follower for f in UserFollow.objects
             .filter(target=u, status__in=FOLLOWING_STATUSES,
                     follower__is_active=True)
             .select_related('follower')])

User.following_users = \
    property(lambda u: [f.target for f in UserFollow.objects
             .filter(follower=u, status__in=FOLLOWING_STATUSES,
                     target__is_active=True)
             .select_related('target')])


def compute_blocked_user_ids_for(user):
    """
    Collects user ids that:
        * Blocked by me.
        * Blocked me.
    Makes two SQL requests. May be it can be cached.
    """
    ids = set()
    if user.is_anonymous:
      return ids
    ids.update(f.target_id for f in UserFollow.objects.filter(
        follower=user, status=UserFollow.BLOCKED))
    ids.update(f.follower_id for f in UserFollow.objects.filter(
        target=user, status=UserFollow.BLOCKED))
    return ids
