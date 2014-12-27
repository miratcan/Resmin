from apps.notification.models import NotificationMeta, NotificationType
from apps.notification.models import _pks_to_str
from django.contrib.contenttypes.models import ContentType


def _new_notification(ntype, sub, obj, recipient, url):
    return NotificationMeta.objects.create(
        ntype=ntype,
        recipient=recipient,
        url=url,
        s_tp=ContentType.objects.get_for_model(sub),
        s_pks=_pks_to_str([sub.pk]),
        o_tp=ContentType.objects.get_for_model(obj),
        o_pks=_pks_to_str([obj.pk]))


def notify(ntype_slug, sub, obj, recipient, url):
    ntype = NotificationType.objects.get(slug=ntype_slug)
    if not ntype.plural:
        return _new_notification(ntype, sub, obj, recipient, url)
    if ntype.plural == NotificationType.PLURAL_SUB:
        nm = NotificationMeta.objects.filter(
            ntype=ntype, recipient=recipient, is_published=False,
            o_tp=ContentType.objects.get_for_model(obj),
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
            s_tp=ContentType.objects.get_for_model(sub),
            s_pks=_pks_to_str([sub.pk])).first()
        if nm:
            nm.add_obj(obj)
            nm.save()
            return nm
        else:
            return _new_notification(ntype, sub, obj, recipient, url)
