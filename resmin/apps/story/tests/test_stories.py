from django.test import TestCase
from django.contrib.auth.models import AnonymousUser
from apps.follow.models import UserFollow
from apps.story.models import Story

from resmin.utils.factories import (
    StoryFactory, UserFactory, UserFollowFactory, QuestionMetaFactory)


class TestStoryBase(TestCase):
    def setUp(self):
        self.u1 = UserFactory()
        self.u2 = UserFactory()
        self.u3 = UserFactory()
        self.au = AnonymousUser()

        self.qm = QuestionMetaFactory(owner=self.u1)

        """ Draft story. """
        self.ds = StoryFactory(
            owner=self.u1, visible_for=Story.VISIBLE_FOR_EVERYONE,
            status=Story.DRAFT, question_meta=self.qm)

        """ Published story. """
        self.ps = StoryFactory(
            owner=self.u1, visible_for=Story.VISIBLE_FOR_EVERYONE,
            status=Story.PUBLISHED, question_meta=self.qm)

        """ User 3 blocks User 1."""
        UserFollowFactory(
            status=UserFollow.BLOCKED, follower=self.u1, target=self.u1)


class TestStoryVisibity(TestStoryBase):

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


class TestStoryListingVisibility(TestStoryBase):

    def test_listing_from_question_meta(self):
        qm = QuestionMetaFactory(owner=self.u1)
        s2 = StoryFactory(owner=self.u1, question_meta=qm)
        qs = Story.objects.build(frm=self.qm, listing='public')
        self.assertEqual(s2 not in qs, True)

    def test_listing_from_user(self):
        qm = QuestionMetaFactory(owner=self.u1)
        s2 = StoryFactory(owner=self.u1, question_meta=qm)
        qs = Story.objects.build(frm=self.u1, listing='public')
        self.assertEqual(qs.count(), 1)

    def test_listing_from_wall(self):
        """ Hey it's good starting point for learning TDD.
            Be bold about sending pull request. """

    def test_listing_from_wall_when_blocked_some_users(self):
        """ Hey it's good starting point for learning TDD.
            Be bold about sending pull request. """
