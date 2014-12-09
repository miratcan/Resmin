from django.db import models


class StoryManager(models.Manager):

    def from_followings(self, user):
        uids = user.following_user_ids
        uids.append(user.id)
        return super(StoryManager, self)\
            .get_queryset()\
            .filter(owner_id__in=uids)

    def from_user(self, user):
        return super(StoryManager, self)\
            .get_queryset()\
            .filter(owner=user)
