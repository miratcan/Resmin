from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from apps.story.models import Story
from apps.notification.models import (
    NotificationMeta, NotificationType,
    notification_preferences as get_notification_preferences)
from apps.notification.utils import notify
from resmin.utils.factories import (
    NotificationTypeFactory, UserFactory, StoryFactory, QuestionMetaFactory)


class TestNotifications(TestCase):
    NTYPE_SLUG = 'existing_notification'

    def setUp(self):
        self.u1 = UserFactory()
        self.u2 = UserFactory()
        self.u3 = UserFactory()
        self.u4 = UserFactory()

        self.qm = QuestionMetaFactory(owner=self.u1)
        self.s = StoryFactory(question_meta=self.qm, owner=self.u1)
        self.nt = NotificationTypeFactory(
            slug=self.NTYPE_SLUG,
            plural=NotificationType.PLURAL_SUB,
            s_ct=ContentType.objects.get_for_model(User),
            o_ct=ContentType.objects.get_for_model(Story),
            is_active=True)

    def test_get_notification_preferences(self):
        npref = get_notification_preferences(
            self.u1.id, self.NTYPE_SLUG)
        self.assertEqual(npref, {})

    def test_throwing_non_existing_notification(self):
        notify('non_existing_notification', None, None, self.u1, None)
        self.assertEqual(NotificationMeta.objects.count(), 0)

    def test_throwing_existing_notification(self):
        notify('existing_notification', self.u2, self.s, self.u1, '/abc/')
        self.assertEqual(NotificationMeta.objects.count(), 1)
