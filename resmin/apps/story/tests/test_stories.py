from django.test import TestCase
from django.contrib.auth.models import AnonymousUser
from apps.follow.models import UserFollow
from apps.story.models import Story

from resmin.utils.factories import (
    StoryFactory, UserFactory, UserFollowFactory, QuestionMetaFactory)


class TestStoryVisibity(TestCase):

    def setUp(self):
        self.u1 = UserFactory()
        self.u2 = UserFactory()
        self.u3 = UserFactory()

        self.qm = QuestionMetaFactory(owner=self.u1)
        self.ds = StoryFactory(
            owner=self.u1, visible_for=Story.VISIBLE_FOR_EVERYONE,
            status=Story.DRAFT, question_meta=self.qm)
        self.ps = StoryFactory(
            owner=self.u1, visible_for=Story.VISIBLE_FOR_EVERYONE,
            status=Story.PUBLISHED, question_meta=self.qm)
        self.au = AnonymousUser()

        """ User 3 blocks User 1."""
        UserFollowFactory(
            status=UserFollow.BLOCKED, follower=self.u1, target=self.u1)

    def test_draft_story_must_be_visible_to_owner(self):

        """ Draft story must not be visible for an anonymouse user."""
        self.assertEqual(self.ds.is_visible_for(self.au), False)

        """ Draft story must not be visible for another. """
        self.assertEqual(self.ds.is_visible_for(self.u2), False)

        """ Draft story must be visible for story owner. """
        self.assertEqual(self.ds.is_visible_for(self.u1), True)

        """ Draft story must not be visible for a blocked user. """
        self.assertEqual(self.ds.is_visible_for(self.u3), False)

    def test_published_story_must_be_visible_for_everyone_but_blocked(self):
        """ Published story must be visible for an anonymouse user. """
        self.assertEqual(self.ps.is_visible_for(self.au), True)

        """ Published story must be visible for another."""
        self.assertEqual(self.ps.is_visible_for(self.u2), True)

        """ Publsihed story must be visible for owner. """
        self.assertEqual(self.ps.is_visible_for(self.u1), True)

        """ Draft story must not be visible for a blocked user. """
        self.assertEqual(self.ds.is_visible_for(self.u3), False)
