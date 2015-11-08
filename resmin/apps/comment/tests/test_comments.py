from django.test import TestCase
from django.contrib.auth.models import AnonymousUser

from apps.follow.models import UserFollow
from apps.comment.models import Comment

from resmin.utils.factories import (
    UserFactory, UserFollowFactory, StoryFactory, QuestionMetaFactory,
    CommentFactory)


class TestCommentListVisibility(TestCase):

    def setUp(self):
        self.u1 = UserFactory()
        self.u2 = UserFactory()
        self.u3 = UserFactory()
        self.au = AnonymousUser()

        """ User 3 blocks User 2."""
        UserFollowFactory(
            status=UserFollow.BLOCKED, follower=self.u3, target=self.u1)

        self.qm = QuestionMetaFactory(owner=self.u1)
        self.st = StoryFactory(owner=self.u1, question_meta=self.qm)

        self.cm1 = CommentFactory(owner=self.u2, story=self.st,
                                  status=Comment.PUBLISHED)
        self.cm2 = CommentFactory(owner=self.u3, story=self.st,
                                  status=Comment.PUBLISHED)

    def test_comments_must_be_visible_for_everyone_but_blocked(self):

        """ First user must NOT see all comments. """

        qs = Comment.objects\
            .from_active_owners()\
            .published()\
            .visible_for(self.u1)\
            .filter(story=self.st)

        self.assertEqual(qs.count(), 1)

        """ Second user must see all comments. """

        qs = Comment.objects\
            .from_active_owners()\
            .published()\
            .visible_for(self.u2)\
            .filter(story=self.st)

        self.assertEqual(qs.count(), 2)

        """ Third user must see all comments. """

        qs = Comment.objects\
            .from_active_owners()\
            .published()\
            .visible_for(self.u3)\
            .filter(story=self.st)

        self.assertEqual(qs.count(), 2)
