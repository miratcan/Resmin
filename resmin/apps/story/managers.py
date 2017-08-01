from django.db.models import Q, Manager
from django.contrib.auth.models import User, AnonymousUser
from ..question.models import QuestionMeta
from ..follow.models import compute_blocked_user_ids_for


class StoryManager(Manager):

    def build(self, requested_user=AnonymousUser(), frm=None,
              listing='public', ordering='recent'):

        if not requested_user.is_authenticated() and listing in \
           ['wall', 'draft']:
            return self.get_queryset.none()

        if listing not in ['public', 'wall', 'draft']:
            listing = 'public'

        if listing == 'public':
            qset = Q(status=self.model.PUBLISHED,
                     owner__is_active=True)
            if not requested_user.is_authenticated():
                qset = qset & Q(is_nsfw=False)
        elif listing == 'wall':
            oids = requested_user.following_user_ids
            oids.append(requested_user.id)
            qset = Q(status=self.model.PUBLISHED,
                     owner_id__in=oids)
        elif listing == 'draft':
            qset = Q(status=self.model.DRAFT, owner=requested_user)

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
                    'recent': '-updated_at'}.get(ordering, '-updated_at')

        return self.get_queryset()\
            .filter(qset)\
            .exclude(owner_id__in=blocked_user_ids)\
            .order_by(ordering)
