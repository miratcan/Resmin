"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from apps.story.models import Story
from apps.notification.models import (NotificationMeta, NotificationType,
                                      SiteNotification)
from apps.notification.utils import notify


def _create_user(username, password):
    return User.objects.create_user(username, username, password)


def _create_story(owner):
    return Story.objects.create(owner=owner)


class SimpleTest(TestCase):

    def setUp(self):
        self.u1 = _create_user('u1', '1')
        self.u2 = _create_user('u2', '1')
        self.u3 = _create_user('u3', '1')
        self.u4 = _create_user('u4', '1')
        self.s1 = _create_story(self.u1)
        NotificationType.objects.update(is_active=True)

    def test_undefined_notification(self):
        notify('non_existing_notification', None, None, None, None)
        self.assertEqual(NotificationMeta.objects.count(), 0)

    def test_user_liked_your_story(self):

        notify('user_liked_your_story', self.u2, self.s1, self.u1, '/abc/')
        self.assertEqual(NotificationMeta.objects.count(), 1)

        nm = NotificationMeta.objects.first()
        self.assertEqual(len(nm.subs), 1)
        nm.publish()
        sn = SiteNotification.objects.first()
        self.assertEqual(
            sn.template_name(),
            'notification/user_liked_your_story/'
            'sub_sing_obj_sing/site_notification.html')
        NotificationMeta.objects.all().delete()
        SiteNotification.objects.all().delete()

    def test_user_liked_your_story_plur_sub(self):

        notify('user_liked_your_story', self.u2, self.s1, self.u1, '/abc/')
        notify('user_liked_your_story', self.u3, self.s1, self.u1, '/abc/')
        notify('user_liked_your_story', self.u4, self.s1, self.u1, '/abc/')
        self.assertEqual(NotificationMeta.objects.count(), 1)

        nm = NotificationMeta.objects.first()
        self.assertEqual(len(nm.subs), 3)

        nm.publish()
        sn = SiteNotification.objects.first()
        self.assertEqual(
            sn.template_name(),
            'notification/user_liked_your_story/'
            'sub_plur_obj_sing/site_notification.html')
