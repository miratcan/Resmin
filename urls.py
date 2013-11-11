from django.conf.urls import patterns, url, include
from django.contrib import admin
from django.conf import settings

from django.views.generic import TemplateView
from apps.question.resources import QuestionResource
from apps.account.resources import UserResource
from tastypie.api import Api

admin.autodiscover()

v1_api = Api(api_name='v1')

v1_api.register(QuestionResource())
v1_api.register(UserResource())

urlpatterns = patterns(
    '',
    url(r'^$',
        'apps.question.views.index',
        name='index'),

    url(r'^f/$', 'apps.question.views.index',
        name='index-from-followings',
        kwargs={'get_filter': 'from_followings'}),

    url(r'^pfr/$', 'apps.account.views.pending_follow_requests',
        name='pending-follow-requests'),

    url(r'^upfr/$', 'apps.account.views.update_pending_follow_request',
        name='update-pending-follow-request'),

    url(r'^fix/$', 'apps.question.views.fix_answers',
        name='fix-answers'),

    url(r'^d/$', 'apps.question.views.index',
        name='index-from-direct',
        kwargs={'get_filter': 'direct'}),

    url(r'^u/(?P<username>[-\w]+)/(?P<action>(block|unblock|follow|unfollow))?/?$',
        'apps.account.views.profile',
        name='profile'),

    url(r'^u/(?P<username>[-\w]+)/to/followings/$',
        'apps.account.views.profile',
        name='my-answers-to-followers',
        kwargs={'get_filter': 'to_followings'}),

    url(r'^u/(?P<username>[-\w]+)/to/others/$',
        'apps.account.views.profile',
        name='my-direct-answers',
        kwargs={'visible_for': 2}),

    url(r'^e/$',
        'apps.account.views.email',
        name='email_form'),

    url(r'^e/(?P<key>[-\w]+)/$',
        'apps.account.views.email',
        name='email_confirm'),

    url(r'^cf/(?P<key>[-\w]+)/$',
        'apps.question.views.cancel_follow',
        name='cancel_follow'),

    url(r'^me/update/$',
        'apps.account.views.update_profile',
        name='update_profile'),

    url(r'^me/key/$',
        'apps.account.views.remote_key',
        name='remote_key'),

    url(r'^p/r/$',
        'django.contrib.auth.views.password_reset',
        name='password_reset',
        kwargs={'template_name': 'auth/password_reset_form.html',
                'subject_template_name': 'emails/password_reset_subject.txt',
                'email_template_name': 'emails/password_reset_body.txt'}
        ),

    url(r'^p/r/sent/$',
        'django.contrib.auth.views.password_reset_done',
        name='password_reset_sent',
        kwargs={'template_name': 'auth/password_reset_sent.html', }
        ),

    url(r'^p/r/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
        'django.contrib.auth.views.password_reset_confirm',
        name='password_reset_confirm',
        kwargs={'post_reset_redirect': '/p/r/done/',
                'template_name': 'auth/password_reset_confirm.html'}
        ),

    url(r'^p/r/done/$',
        'django.contrib.auth.views.password_reset_complete',
        name='password_reset_complete',
        kwargs={'template_name': 'auth/password_reset_done.html'}),

    url(r'^q/$',
        'apps.question.views.questions',
        name='questions'),

    url(r'^q/(?P<base62_id>[-\w]+)/$',
        'apps.question.views.question',
        name='question'),

    url(r'^q/(?P<base62_id>[-\w]+)/f/$',
        'apps.question.views.question',
        name='question-detail-from-followings',
        kwargs={'get_filter': 'followings'}),


    url(r'^q/(?P<base62_id>[-\w]+)/delete/$',
        'apps.question.views.question',
        name='delete_question',
        kwargs={'show_delete': True}),


    url(r'q/(?P<base62_id>[-\w]+)/d/^$',
        'apps.question.views.question',
        name='index',
        kwargs={'get_filter': 'direct'}),

    url(r'^a/(?P<base62_id>[-\w]+)/$',
        'apps.question.views.answer',
        name='answer'),

    url(r'^a/(?P<base62_id>[-\w]+)/update/$',
        'apps.question.views.update_answer',
        name='update-answer'),

    url(r'^r/$',
        'apps.question.views.random',
        name='random'),

    url(r'^reg/$',
        'apps.account.views.register',
        name='register'),

    url(r'^login/$',
        'django.contrib.auth.views.login',
        name='login', kwargs={'template_name': 'auth/login.html'}),

    url(r'^logout/$',
        'django.contrib.auth.views.logout',
        name='logout', kwargs={'next_page': '/'}),

    url(r'^i/$',
        'apps.account.views.invitations',
        name='invitations'),

    url(r'^l/$',
        'apps.question.views.like',
        name='like'),

    (r'^fix_answer', 'apps.question.views.fix_answer'),

    url(r'^hof/$',
        'apps.account.views.hof',
        name='hof'),

    url(r'^test/$',
        TemplateView.as_view(template_name="test.html"),
        name='test'),

    url(r'^adminmisinlansen/',
        include(admin.site.urls)),

    (r'^api/', include(v1_api.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns(
        '',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT, }),
        url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.STATIC_ROOT, }),
    )
