from apps.notification.models import Notification


class NotificationMiddleware(object):
    def process_view(self, request, view_func, view_args, view_kwargs):
        nid = request.GET.get('nid')
        if nid:
            Notification.objects.filter(recipient=request.user,
                                        id=nid).delete()

        return view_func(request, *view_args, **view_kwargs)
