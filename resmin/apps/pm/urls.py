from django.conf.urls import url
from django.views.generic import RedirectView
import views

urlpatterns = [
    url(r'^$', RedirectView.as_view(url='inbox/'), name='messages_redirect'),
    url(r'^inbox/$',
        views.inbox, name='messages_inbox'),
    url(r'^outbox/$',
        views.outbox, name='messages_outbox'),
    url(r'^compose/$',
        views.compose, name='messages_compose'),
    url(r'^compose/(?P<recipient>[\w.@+-]+)/$',
        views.compose, name='messages_compose_to'),
    url(r'^reply/(?P<message_id>[\d]+)/$',
        views.reply, name='messages_reply'),
    url(r'^view/(?P<message_id>[\d]+)/$',
        views.view, name='messages_detail'),
    url(r'^delete/(?P<message_id>[\d]+)/$',
        views.delete, name='messages_delete'),
    url(r'^undelete/(?P<message_id>[\d]+)/$',
        views.undelete, name='messages_undelete'),
    url(r'^trash/$',
        views.trash, name='messages_trash'),
]
