from django.conf.urls import patterns, url
from django.views.generic import RedirectView

urlpatterns = patterns(
    '',
    url(r'^$', RedirectView.as_view(url='inbox/'), name='messages_redirect'),
    url(r'^inbox/$',
        'apps.pm.views.inbox', name='messages_inbox'),
    url(r'^outbox/$',
        'apps.pm.views.outbox', name='messages_outbox'),
    url(r'^compose/$',
        'apps.pm.views.compose', name='messages_compose'),
    url(r'^compose/(?P<recipient>[\w.@+-]+)/$',
        'apps.pm.views.compose', name='messages_compose_to'),
    url(r'^reply/(?P<message_id>[\d]+)/$',
        'apps.pm.views.reply', name='messages_reply'),
    url(r'^view/(?P<message_id>[\d]+)/$',
        'apps.pm.views.view', name='messages_detail'),
    url(r'^delete/(?P<message_id>[\d]+)/$',
        'apps.pm.views.delete', name='messages_delete'),
    url(r'^undelete/(?P<message_id>[\d]+)/$',
        'apps.pm.views.undelete', name='messages_undelete'),
    url(r'^trash/$',
        'apps.pm.views.trash', name='messages_trash'),
)
