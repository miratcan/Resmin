from json_field.fields import JSONField

from django.db import models
from django.core.cache import get_cache
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render
from django.template.loader import render_to_string

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
        max_length=32,
        null=True,
        blank=True, choices=((PLURAL_SUB, 'Subject'),
                             (PLURAL_OBJ, 'Object'),
                             (PLURAL_BOTH, 'Both')))

    def get_option_name(self):
        return render('notification/%s/option.txt')

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
        cache.remove(self.cache_key(self.user_id, self.ntype.slug))

    def __unicode__(self):
        return '%s\'s preferences on "%s" notifications' % (
            self.user, self.ntype)


class NotificationMeta(models.Model):
    ntype = models.ForeignKey(NotificationType)
    recipient = models.ForeignKey(User, related_name='recipient')
    s_tp = models.ForeignKey(ContentType, related_name='s_tp')
    o_tp = models.ForeignKey(ContentType, related_name='o_tp')
    s_pks = models.CommaSeparatedIntegerField(max_length=4096)
    o_pks = models.CommaSeparatedIntegerField(max_length=4096)
    url = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)
    custom_message = models.TextField(null=True, blank=True)
    is_published = models.BooleanField(default=False)

    def _get_objects(self, c_tp, pks):
        pks = _str_to_pks(pks)
        return c_tp.model_class().objects.filter(pk__in=pks)

    def _add_object(self, key, obj):
        CT_MAP = {'sub': {'ct': 's_tp', 'pks': 's_pks'},
                  'obj': {'ct': 's_tp', 'pks': 's_pks'}}
        ct_key, pks_key = CT_MAP[key]['ct'], CT_MAP[key]['pks']
        o_ct = ContentType.objects.get_for_model(obj)
        if o_ct != getattr(self, ct_key):
            raise ValueError(
                'This %s must be %s instance.' % (
                    key, self.s_tp.model))
        pks = list(_str_to_pks(getattr(self, pks_key)))
        if obj.pk not in pks:
            pks.append(obj.pk)
        setattr(self, pks_key, _pks_to_str(pks))
        self.save()

    def add_sub(self, sub):
        self._add_object('sub', sub)

    def add_obj(self, obj):
        self._add_object('obj', obj)

    @property
    def subs(self):
        return self._get_objects(self.s_tp, self.s_pks)

    @property
    def objs(self):
        return self._get_objects(self.o_tp, self.o_pks)

    class Meta:
        verbose_name_plural = "notification metas"

    def __unicode__(self):
        return "'%s' notification for %s" % (self.ntype, self.recipient)


class EmailNotification(models.Model):
    meta = models.ForeignKey(NotificationMeta)
    subject = models.CharField(max_length=255, blank=True)
    body_txt = models.TextField(blank=True)
    body_html = models.TextField(blank=True)
    is_sent = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    def subject_tname(self):
        return 'notification/%s/email_subject.txt' % self.meta.ntype.slug

    def _body_tname(self, subdir, postfix):
        'notification/%s/email_%s.txt' % (subdir, postfix)

    def body_txt_tname(self):
        return self._body_tname(self.meta.ntype.slug, 'txt')

    def body_html_tname(self):
        return self._body_tname(self.meta.ntype.slug, 'html')

    def save(self, *args, **kwargs):
        self.subject = render_to_string(
            self.subject_tname(), {'notification': self.meta})
        self.body_txt = render_to_string(
            self.body_txt_tname(), {'notification': self.meta})
        self.body_html = render_to_string(
            self.body_html_tname(), {'notification': self.meta})
        super(EmailNotification, self).save(*args, **kwargs)


class SiteNotification(models.Model):
    meta = models.ForeignKey(NotificationMeta)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)


def notification_preference(user_id, ntype_slug, use_cache=True):
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
        print ntype, ntype.default_preferences
        p = NotificationPreference.objects.create(
            user_id=user_id,
            ntype=ntype,
            preferences=ntype.default_preferences).preferences
    if use_cache:
        cache.set(cache_key, p, 60)
    return p
