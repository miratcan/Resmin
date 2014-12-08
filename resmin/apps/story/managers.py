from django.db import models


class StoryManager(models.Manager):

    def from_followings(self, user):
        user_ids = user.following_user_ids
        user_ids.append(user.id)
        return super(StoryManager, self)\
            .get_queryset()\
            .filter(owner_id__in=user_ids)

    def from_question_meta(self, question_meta):
        return super(StoryManager, self)\
            .get_queryset()\
            .filter(mounted_question_metas=question_meta)
