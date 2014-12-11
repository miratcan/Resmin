from django.db import models


class StoryManager(models.Manager):

    def from_followings(self, user):
        uids = user.following_user_ids
        uids.append(user.id)
        return super(StoryManager, self)\
            .get_query_set()\
            .filter(owner_id__in=uids)

    def from_user(self, user):
        return super(StoryManager, self)\
            .get_query_set()\
            .filter(owner=user)

    def from_question_meta(self, qm):
        return super(StoryManager, self)\
            .get_query_set()\
            .filter(mounted_question_metas=qm)
