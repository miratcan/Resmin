from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.notification.models import SiteNotification, NotificationMeta

from resmin.libs.shortcuts import render_to_json

@login_required
def notifications(request):
    return render(request, 'notification/list.html', {
        'notifications': SiteNotification.objects.filter(
            meta__recipient=request.user, meta__is_read=False)})

@login_required
def mark_as_read(request):
    resp = {'status'}
    if request.method == 'POST' and 'pk' in request.POST:
        nid = request.POST['pk']
        nmeta = NotificationMeta.objects.get(sitenotification=nid)
        nmeta.is_read = True
        nmeta.save(update_fields=['is_read'])
        return render_to_json({'success': True})
    return render_to_json({'success': False,
                           'message': 'Invalida data'})
