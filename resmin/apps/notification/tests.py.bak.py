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

    def test_undefined_notification(self):

        # No NotificationMeta objects must be created.
        notify('non_existing_notification', None, None, None, None)
        self.assertEqual(NotificationMeta.objects.count(), 0)

    def test_user_liked_my_answer(self):

        # When user_user_liked_my_answer created.
        notify('user_liked_my_answer', self.u2, self.s1, self.u1, '/abc/')

        # There must be a NotificationMeta object.
        self.assertEqual(NotificationMeta.objects.count(), 1)

        # And that NotificationMeta must have 1 sub.
        nm = NotificationMeta.objects.first()
        self.assertEqual(len(nm.subs), 1)

        # When that notificationMeta is published.
        nm.publish()

        # SiteNotification object must be created.
        sn = SiteNotification.objects.first()
        self.assertEqual(
            sn.template_name(),
            'notification/user_liked_my_answer/'
            'sub_sing_obj_sing/site_notification.html')

        # Cleanup...
        NotificationMeta.objects.all().delete()
        SiteNotification.objects.all().delete()

    def test_user_liked_own_answer(self):

        # When user likes his/her own story.
        notify('user_liked_my_answer', self.u2, self.s1, self.u1, '/abc/',
               ignored_recipients=[self.u1])

        # There must be no NotificationMeta objects created.
        self.assertEqual(NotificationMeta.objects.count(), 0)

    def test_user_liked_your_story_answer_with_multiple_subjects(self):

        # When 
        notify('user_liked_my_answer', self.u2, self.s1, self.u1, '/abc/')
        notify('user_liked_my_answer', self.u3, self.s1, self.u1, '/abc/')
        notify('user_liked_my_answer', self.u4, self.s1, self.u1, '/abc/')
        self.assertEqual(NotificationMeta.objects.count(), 1)

        nm = NotificationMeta.objects.first()
        self.assertEqual(len(nm.subs), 3)
        nm.publish()
        sn = SiteNotification.objects.first()
        self.assertEqual(
            sn.template_name(),
            'notification/user_liked_my_answer/'
            'sub_plur_obj_sing/site_notification.html')
