from json_field.fields import JSONField

from django.db import models
from django.core.cache import get_cache
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string
from django.template import TemplateDoesNotExist

cache = get_cache('default')


def _str_to_pks(s):
    return [] if s == '' else (int(pk) for pk in s.split(','))


def _pks_to_str(pks):
    return ','.join((str(pk) for pk in pks))


class NotificationType(models.Model):

    PLURAL_OBJ = 'obj'
    PLURAL_SUB = 'sub'
    PLURAL_BOTH = 'both'

    slug = models.SlugField(max_length=255)
    name = models.CharField(max_length=255)
    default_preferences = JSONField()
    plural = models.CharField(
        max_length=32, null=True, blank=True,
        choices=((PLURAL_SUB, 'Subject'), (PLURAL_OBJ, 'Object'),
                 (PLURAL_BOTH, 'Both')))
    s_ct = models.ForeignKey(ContentType, verbose_name='Subject Content Type',
                             related_name='s_ct')
    o_ct = models.ForeignKey(ContentType, verbose_name='Object Content Type',
                             related_name='o_ct')
    is_active = models.BooleanField(default=True)

    def get_template_prefix(self, multiple_subs=False, multiple_objs=False):
        """
        Return template name prefix based on plurality of subject and
        objects.
        """
        SINGULAR_KEY = 'sing'
        PLURAL_KEY = 'plur'
        pfx = self.slug  # prefix
        sub = 'sub_%s' % (PLURAL_KEY if multiple_subs else SINGULAR_KEY)
        obj = 'obj_%s' % (PLURAL_KEY if multiple_objs else SINGULAR_KEY)
        return 'notification/%s/%s_%s/' % (pfx, sub, obj)

    def __unicode__(self):
        return self.name


class NotificationPreference(models.Model):

    user = models.ForeignKey(User)
    ntype = models.ForeignKey(NotificationType)
    preferences = JSONField()

    @staticmethod
    def cache_key(user_id, preference_slug):
        return 'user:%s:preferences:%s' % (user_id, preference_slug)

    def save(self, *args, **kwargs):
        super(NotificationPreference, self).save(*args, **kwargs)
        cache.delete(self.cache_key(self.user_id, self.ntype.slug))

    def __unicode__(self):
        return '%s\'s preferences on "%s" notifications' % (
            self.user, self.ntype)


class NotificationMeta(models.Model):

    ntype = models.ForeignKey(NotificationType)
    recipient = models.ForeignKey(User, related_name='recipient')
    s_pks = models.CommaSeparatedIntegerField(
        verbose_name='Subject Pks', max_length=4096)
    o_pks = models.CommaSeparatedIntegerField(
        verbose_name='Object Pks', max_length=4096)
    url = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)

    def _get_objects(self, c_tp, pks):
        """
        Generic method for getting comma seperated objects.
        """
        pks = _str_to_pks(pks)
        return c_tp.model_class().objects.filter(pk__in=pks)

    def _add_object(self, key, obj):
        """
        Generic method for adding comma seperated object.
        """
        CT_MAP = {'sub': {'ct': 's_ct', 'pks': 's_pks'},
                  'obj': {'ct': 'o_ct', 'pks': 's_pks'}}
        ct_key, pks_key = CT_MAP[key]['ct'], CT_MAP[key]['pks']
        o_ct = ContentType.objects.get_for_model(obj)
        if o_ct != getattr(self.ntype, ct_key):
            raise ValueError(
                'This %s must be %s instance.' % (
                    key, self.ntype.s_ct.model))
        pks = list(_str_to_pks(getattr(self, pks_key)))
        if obj.pk not in pks:
            pks.append(obj.pk)
        setattr(self, pks_key, _pks_to_str(pks))

    def _has_multiple_objects(self, key):
        """
        Return True if comma seperated objects in given key has more than
        one object.
        """
        return ',' in getattr(self, key)

    def add_sub(self, sub):
        """
        Adds subject to notificationMeta instance. Must be saved later.
        """
        self._add_object('sub', sub)

    def add_obj(self, obj):
        """
        Adds object to notificationMeta instance. Must be saved later.
        """
        self._add_object('obj', obj)

    @property
    def multiple_subs(self):
        """
        Return True if notification has more than one subjects.
        """
        return self._has_multiple_objects('s_pks')

    @property
    def multiple_objs(self):
        """
        Return True if notification has more than one objects.
        """
        return self._has_multiple_objects('o_pks')

    @property
    def subs(self):
        """
        Return subjects of notification.
        """
        return self._get_objects(self.ntype.s_ct, self.s_pks)

    @property
    def objs(self):
        """
        Return objects of notification.
        """
        return self._get_objects(self.ntype.o_ct, self.o_pks)

    @property
    def sub(self):
        """
        Return first subject. Usually used with notification types 
        with singular subjects.
        """
        return self.subs[0]

    @property
    def obj(self):
        """
        Return first object. Usually used with notification types 
        with singular subjects.
        """
        return self.objs[0]

    def _publish_site_notification(self):
        """
        Publish site notification.
        """
        return SiteNotification.objects.create(meta=self)

    def _publish_email_notification(self):
        """
        Publish email notification.
        """
        return EmailNotification.objects.create(meta=self)

    def get_notification_template(self):
        """
        Return notification template prefix for this notification type.
        """
        return self.ntype.get_notification_template(self.multiple_subs,
                                                    self.multiple_objs)

    def get_url(self):
        """
        Return special url that used to set read notification meta.
        """
        return '%s?nid=%s' % (self.url, self.id)

    def get_template_prefix(self):
        return self.ntype.get_template_prefix(self.multiple_subs,
                                              self.multiple_objs)

    def publish(self):
        """
        Publish this notification. Create SiteNotification and
        EmailNotification objects if requested at NotificationPreference
        of user.
        """
        preferences = notification_preferences(
            self.recipient.pk, self.ntype.slug)
        if preferences.get('send_mail'):
            self._publish_email_notification()
        if self.recipient.email and preferences.get('send_site_notification'):
            self._publish_site_notification()
        self.is_published = True
        self.save()

    class Meta:
        verbose_name_plural = "notification metas"

    def __unicode__(self):
        return "'%s' notification for %s" % (self.ntype, self.recipient)


class EmailNotification(models.Model):
    meta = models.ForeignKey(NotificationMeta)
    subject = models.CharField(max_length=255, blank=True)
    body_txt = models.TextField(blank=True)
    body_html = models.TextField(null=True, blank=True)
    is_sent = models.BooleanField(default=False)

    def _body_tname(self, postfix):
        """
        Generic method for getting body template name.
        """
        return '%s/email_body.%s' % (self.meta.get_template_prefix(),
                                     postfix)

    def subject_tname(self):
        """
        Return subject template name.
        """
        return '%s%s' % (self.meta.get_template_prefix(),
                         'email_subject.txt')

    def body_txt_tname(self):
        """
        Return txt version of body template.
        """
        return self._body_tname('txt')

    def body_html_tname(self):
        """
        Return html version of body template.
        """
        return self._body_tname('html')

    def save(self, *args, **kwargs):
        """
        Render, save and send EmailNotification. If dry=True, it will be only \
        rendered and saved.
        """
        dry = kwargs.pop('dry')
        ctx = {'nm': self.meta,
               'site': Site.objects.get_current()}
        self.subject = render_to_string(self.subject_tname(), ctx)
        self.body_txt = render_to_string(self.body_txt_tname(), ctx)
        try:
            self.body_html = render_to_string(self.body_html_tname(), ctx)
        except TemplateDoesNotExist:
            pass
        super(EmailNotification, self).save(*args, **kwargs)
        if not dry:
            send_mail(self.subject,
                      self.body_txt,
                      settings.DEFAULT_FROM_EMAIL
                      [self.meta.recipient.email], fail_silently=False)


class SiteNotification(models.Model):
    meta = models.ForeignKey(NotificationMeta)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    def template_name(self):
        return '%s%s' % (self.meta.get_template_prefix(),
                         'site_notification.html')


def notification_preferences(user_id, ntype_slug, use_cache=True):
    if use_cache:
        cache_key = NotificationPreference.cache_key(user_id, ntype_slug)
        cached = cache.get(cache_key)
        if cached:
            return cached
    try:
        p = NotificationPreference.objects.get(
            user_id=user_id, ntype__slug=ntype_slug).preferences
    except NotificationPreference.DoesNotExist:
        ntype = NotificationType.objects.get(slug=ntype_slug)
        p = NotificationPreference.objects.create(
            user_id=user_id,
            ntype=ntype,
            preferences=ntype.default_preferences).preferences
    if use_cache:
        cache.set(cache_key, p, 60)
    return p
