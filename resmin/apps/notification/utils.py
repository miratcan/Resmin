from apps.notification.models import NotificationMeta, NotificationType
from apps.notification.models import _pks_to_str
from logging import getLogger

logger = getLogger(__name__)


def _new_notification(ntype, sub, obj, recipient, url):
    return NotificationMeta.objects.create(
        ntype=ntype,
        recipient=recipient,
        url=url,
        s_pks=_pks_to_str([sub.pk]),
        o_pks=_pks_to_str([obj.pk]))


def notify(ntype_slug, sub, obj, recipient, url,
           ignored_recipients=[]):

    if recipient in ignored_recipients:
        return

    try:
        ntype = NotificationType.objects.get(slug=ntype_slug)
    except NotificationType.DoesNotExist:
        logger.error('NotificationType with slug "%s" not found.' % ntype_slug)
        return

    if not ntype.is_active:
        return

    if not ntype.plural:
        return _new_notification(ntype, sub, obj, recipient, url)

    if ntype.plural == NotificationType.PLURAL_SUB:
        nm = NotificationMeta.objects.filter(
            ntype=ntype, recipient=recipient, is_published=False,
            o_pks=_pks_to_str([obj.pk])).first()
        if nm:
            nm.add_sub(sub)
            nm.save()
            return nm
        else:
            return _new_notification(ntype, sub, obj, recipient, url)

    if ntype.plural == NotificationType.PLURAL_OBJ:
        nm = NotificationMeta.objects.filter(
            ntype=ntype, recipient=recipient, is_published=False,
            s_pks=_pks_to_str([sub.pk])).first()
        if nm:
            nm.add_obj(obj)
            nm.save()
            return nm
        else:
            return _new_notification(ntype, sub, obj, recipient, url)
