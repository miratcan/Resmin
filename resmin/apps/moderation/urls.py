from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    url(r'^c/q/(?P<base62_id>[-\w]+)/$',
        'apps.moderation.views.complain_question', name='complain_qmeta'),
)
