from django.db import models


class StoryManager(models.Manager):

    def from_followings(self, user):
        return super(StoryManager, self)\
            .get_queryset()\
            .filter(owner_id__in=user.following_user_ids)
