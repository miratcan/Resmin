from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.notification.models import SiteNotification


@login_required
def notifications(request):
    return render(request, 'notification/list.html', {
        'notifications': SiteNotification.objects.filter(
            recipient=request.user)})
