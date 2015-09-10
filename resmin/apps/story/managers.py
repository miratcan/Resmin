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

        if listing not in ['public', 'wall', 'private', 'draft']:
            listing = 'public'

        if listing == 'public':
            qset = Q(status=Story.PUBLISHED,
                     visible_for=Story.VISIBLE_FOR_EVERYONE,
                     owner__is_active=True)
            if not requested_user.is_authenticated():
                qset = qset & Q(is_nsfw=False)
        elif listing == 'wall':
            oids = requested_user.following_user_ids
            oids.append(requested_user.id)
            qset = Q(status=Story.PUBLISHED,
                     visible_for=Story.VISIBLE_FOR_EVERYONE,
                     owner_id__in=oids)
        elif listing == 'private':
            oids = requested_user.following_user_ids
            oids.append(requested_user.id)
            qset = Q(status=Story.PUBLISHED,
                     visible_for=Story.VISIBLE_FOR_FOLLOWERS,
                     owner_id__in=oids)
        elif listing == 'draft':
            qset = Q(status=Story.DRAFT, owner=requested_user)

        if frm:
            if isinstance(frm, QuestionMeta):
                qset = qset & Q(question_meta=frm)
            if isinstance(frm, User):
                qset = qset & Q(owner=frm, is_anonymouse=False)

        if requested_user.is_authenticated():
            blocked_user_ids = compute_blocked_user_ids_for(requested_user)
        else:
            blocked_user_ids = []

        ordering = {'popular': '-like_count',
                    'featured': 'is_featured',
                    'recent': '-created_at'}.get(ordering, '-updated_at')

        return Story.objects\
            .filter(qset)\
            .exclude(owner_id__in=blocked_user_ids)\
            .order_by(ordering)
