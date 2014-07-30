from apps.notification.models import Notification, NotificationType


def notify(actor, ntype, target, recipient, url):
    ntype = NotificationType.objects.get(slug=ntype)
    return Notification.objects.create(
        actor=actor, ntype=ntype, target=target,
        recipient=recipient, url=url)