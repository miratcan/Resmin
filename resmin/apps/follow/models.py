from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.db import models

from libs import key_generator


class FollowBase(models.Model):
    follower = models.ForeignKey(User)

    class Meta:
        abstract = True


class QuestionFollow(FollowBase):
    target = models.ForeignKey('question.Question', related_name='question')
    status = models.PositiveSmallIntegerField(
        default=0, choices=((0, 'Following'),
                            (1, 'Unfollowed')))
    key = models.CharField(max_length=255, blank=True)
    reason = models.CharField(max_length=16,
                              choices=(('asked', 'Asked'),
                                       ('answered', 'Answered')))

    def __unicode__(self):
        return '%s %s %s' % (self.follower, self.reason, self.target)

    def save(self, *args, **kwargs):
        self.key = key_generator(size=10)
        super(QuestionFollow, self).save(*args, **kwargs)

    def cancellation_url(self):
        return reverse('cancel_follow', kwargs={'key': self.key})


class UserFollow(FollowBase):
    target = models.ForeignKey(User, related_name='user')
    status = models.PositiveSmallIntegerField(
        default=0, choices=((0, 'Pending'),
                            (1, 'Following'),
                            (2, 'Blocked')))


User.is_blocked = lambda u, t: bool(
    UserFollow.objects.filter(follower=u, target=t, status=2).exists())

User.is_blocked_by = lambda u, t: bool(
    UserFollow.objects.filter(follower=t, target=u, status=2).exists())

User.is_following = lambda u, t: UserFollow.objects.filter(
    follower=u, target=t, status=1).exists()

User.has_pending_follow_request = lambda u, t: \
    UserFollow.objects.filter(follower=u, target=t, status=0).exists()

User.follower_user_ids = \
    property(lambda u: [f.follower_id for f in UserFollow.objects.filter(	
             target=u, status=1)])

User.following_user_ids = \
    property(lambda u: [f.target_id for f in UserFollow.objects.filter(
             follower=u, status=1)])


def compute_blocked_user_ids_for(user):
    ids = set()
    ids.update(f.target_id for f in UserFollow.objects.filter(
        follower=user, status=2))
    ids.update(f.follower_id for f in UserFollow.objects.filter(
        target=user, status=2))
    return ids
