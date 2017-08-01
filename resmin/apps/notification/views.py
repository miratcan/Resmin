from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http.response import JsonResponse
from .models import SiteNotification, NotificationMeta


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
        return JsonResponse({'success': True})
    return JsonResponse({'success': False,
                         'message': 'Invalida data'}, status=400)
