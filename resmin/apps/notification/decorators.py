import functools
from apps.notification.models import Notification


def delete_notification(method):
    @functools.wraps(method)
    def wrapper(request, *args, **kwargs):
        nid = request.GET.get('nid')
        if nid:
            Notification.objects.filter(recipient=request.user,
                                        id=nid).delete()
        return method(request, *args, **kwargs)
    return wrapper
