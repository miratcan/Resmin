from django.test import TestCase
from django.contrib.auth.models import User, AnonymousUser
from apps.story.models import Story
from apps.follow.models import UserFollow


def _create_user(username, password):
    return User.objects.create_user(username, username, password)


class TestStoryIsVisibleFor(TestCase):

    def setUp(self):
        self.u1 = _create_user('u1', '1')
        self.u2 = _create_user('u2', '1')

    def test_draft(self):

        s = Story(owner=self.u1, visible_for=Story.VISIBLE_FOR_EVERYONE,
                  status=Story.DRAFT)
        au = AnonymousUser()

        self.assertEqual(s.is_visible_for(au), False)
        self.assertEqual(s.is_visible_for(self.u1), True)
        self.assertEqual(s.is_visible_for(self.u2), False)

        s.visible_for = Story.VISIBLE_FOR_FOLLOWERS

        self.assertEqual(s.is_visible_for(au), False)
        self.assertEqual(s.is_visible_for(self.u1), True)
        self.assertEqual(s.is_visible_for(self.u2), False)

        UserFollow.objects.create(follower=self.u2, target=self.u1,
                                  status=UserFollow.FOLLOWING)

        self.assertEqual(s.is_visible_for(au), False)
        self.assertEqual(s.is_visible_for(self.u1), True)
        self.assertEqual(s.is_visible_for(self.u2), False)

    def test_published(self):

        s = Story(owner=self.u1, visible_for=Story.VISIBLE_FOR_EVERYONE,
                  status=Story.PUBLISHED)
        au = AnonymousUser()

        self.assertEqual(s.is_visible_for(au), True)
        self.assertEqual(s.is_visible_for(self.u1), True)
        self.assertEqual(s.is_visible_for(self.u2), True)

        s.visible_for = Story.VISIBLE_FOR_FOLLOWERS

        self.assertEqual(s.is_visible_for(au), False)
        self.assertEqual(s.is_visible_for(self.u1), True)
        self.assertEqual(s.is_visible_for(self.u2), False)

        UserFollow.objects.create(follower=self.u2, target=self.u1,
                                  status=UserFollow.FOLLOWING)

        self.assertEqual(s.is_visible_for(au), False)
        self.assertEqual(s.is_visible_for(self.u1), True)
        self.assertEqual(s.is_visible_for(self.u2), True)
