import functools
from apps.notification.models import NotificationMeta


def delete_notification(method):
    @functools.wraps(method)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated():
            nid = request.GET.get('nid')
            if nid:
                NotificationMeta.objects.filter(
                    recipient=request.user, id=nid).update(
                    is_read=True)
        return method(request, *args, **kwargs)
    return wrapper
