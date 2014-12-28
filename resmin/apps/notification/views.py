from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.notification.models import SiteNotification


@login_required
def notifications(request):
    return render(request, 'notification/list.html', {
        'notifications': SiteNotification.objects.filter(
            meta__recipient=request.user, meta__is_read=False)})
