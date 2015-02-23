from django.db.models import Q, Manager
from django.contrib.auth.models import User, AnonymousUser
from apps.follow.models import compute_blocked_user_ids_for


class StoryManager(Manager):

    def build(self, requested_user=AnonymousUser(), frm=None,
              listing='public', ordering='recent'):

        from apps.question.models import QuestionMeta
        from apps.story.models import Story

        if not requested_user.is_authenticated() and listing in \
           ['wall', 'private', 'draft']:
            return Story.objects.none()

        if listing == 'public':
            qset = Q(status=Story.PUBLISHED,
                     visible_for=Story.VISIBLE_FOR_EVERYONE)
            if not requested_user.is_authenticated():
                qset = qset & Q(is_nsfw=True)
        elif listing == 'wall':
            qset = Q(status=Story.PUBLISHED,
                     visible_for=Story.VISIBLE_FOR_EVERYONE,
                     owner_id__in=requested_user.following_user_ids)
        elif listing == 'private':
            qset = Q(status=Story.PUBLISHED,
                     visible_for=Story.VISIBLE_FOR_FOLLOWERS,
                     owner_id__in=requested_user.following_user_ids)
        elif listing == 'draft':
            qset = Q(status=Story.DRAFT, owner=requested_user)
        else:
            qset = Q()

        if frm:
            if isinstance(frm, QuestionMeta):
                qset = qset & Q(mounted_question_metas=frm)
            if isinstance(frm, User):
                qset = qset & Q(owner=frm)

        if requested_user.is_authenticated():
            blocked_user_ids = compute_blocked_user_ids_for(requested_user)
        else:
            blocked_user_ids = []

        ordering = {'popular': '-like_count',
                    'featured': 'is_featured',
                    'recent': '-created_at'}.get(ordering, '-created_at')

        return Story.objects\
            .filter(qset)\
            .exclude(owner_id__in=blocked_user_ids)\
            .order_by(ordering)
