from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings

from django.views.generic import TemplateView


admin.autodiscover()

from django.contrib.sitemaps import Sitemap
from apps.question.models import QuestionMeta
from apps.story.models import Story
from apps.story.api_views import PublicStoryList, UserStoryList, UserList


class QMetaSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.5

    def items(self):
        return QuestionMeta.objects.filter(
            status=QuestionMeta.PUBLISHED)

    def lastmod(self, obj):
        return obj.created_at


class StorySiteMap(Sitemap):
    changefreq = "hourly"
    priority = 0.8

    def items(self):
        return Story.objects.filter(
            status=Story.PUBLISHED)

    def lastmod(self, obj):
        return obj.created_at


urlpatterns = [
    '',
    url(r'^$',
        'apps.question.views.index',
        name='index', kwargs={'listing': 'wall'}),

    url(r'^public/$',
        'apps.question.views.index',
        name='index-public', kwargs={'listing': 'public'}),

    url(r'^pfr/$', 'apps.account.views.pending_follow_requests',
        name='pending-follow-requests'),

    url(r'^pfra/$', 'apps.account.views.pending_follow_request_action',
        name='pending-follow-request-action'),

    url(r'^u/(?P<username>[-\w]+)/(?P<action>(block|unblock|follow|unfollow))?/?$',
        'apps.account.views.profile',
        name='profile'),

    url(r'^u/(?P<username>[-\w]+)/followers/$',
        'apps.account.views.followers',
        name='followers'),

    url(r'^u/(?P<username>[-\w]+)/followings/$',
        'apps.account.views.followings',
        name='followings'),

    url(r'^u/(?P<username>[-\w]+)/draft/',
        'apps.account.views.profile',
        name='profile-drafts',
        kwargs={'listing': 'draft'}),

    url(r'^e/$',
        'apps.account.views.email',
        name='email_form'),

    url(r'^e/(?P<key>[-\w]+)/$',
        'apps.account.views.email',
        name='email_confirm'),

    url(r'^c/(?P<cid>[-\d]+)/$',
        'apps.comment.views.get_comment',
        name='get_comment'),

    url(r'^c/u/(?P<cid>[-\d]+)/$',
        'apps.comment.views.update_comment',
        name='update_comment'),

    url(r'^c/d/(?P<cid>[-\d]+)/$',
        'apps.comment.views.delete_comment',
        name='delete_comment'),

    url(r'^me/update/$',
        'apps.account.views.update_profile',
        name='update_profile'),

    url(r'^me/notification/preferences/$',
        'apps.account.views.notification_preferences',
        name='update_notification_preferences'),

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

    url(r'^p/r/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$',
        'django.contrib.auth.views.password_reset_confirm',
        name='password_reset_confirm',
        kwargs={'post_reset_redirect': '/p/r/complete/',
                'template_name': 'auth/password_reset_confirm.html'}),

    url(r'^p/r/done/$',
        'django.contrib.auth.views.password_reset_done',
        name='password_reset_done',
        kwargs={'template_name': 'auth/password_reset_done.html'}),

    url(r'^p/r/complete/$',
        'django.contrib.auth.views.password_reset_complete',
        name='password_reset_complete',
        kwargs={'template_name': 'auth/password_reset_complete.html'}),

    url(r'^q/(?P<base62_id>[-\w]+)/answer/$',
        'apps.story.views.create_story',
        name='create-story'),

    url(r'^q/(?P<base62_id>[-\w]+)/complain/$',
        'apps.question.views.complain_question',
        name='complain-question'),

    url(r'^q/(?P<base62_id>[-\w]+)(?:/(?P<ordering>[a-zA-Z]+))?/$',
        'apps.question.views.question',
        name='question'),

    url(r'^upload/$',
        'apps.story.views.get_upload', name='get_upload'),

    url(r'^upload/(?P<upload_id>[-\w]+)/$',
        'apps.story.views.upload',
        name='upload'),

    url(r'^q/(?P<base62_id>[-\w]+)/delete/$',
        'apps.question.views.question',
        name='delete_question',
        kwargs={'show_delete': True}),

    url(r'^s/(?P<base62_id>[-\w]+)/$',
        'apps.story.views.story',
        name='story'),

    url(r'^s/(?P<base62_id>[-\w]+)/ui/$',
        'apps.story.views.update_story',
        name='update-images-of-story'),

    url(r'^s/(?P<base62_id>[-\w]+)/ud/$',
        'apps.story.views.update_details',
        name='update-details-of-story'),

    url(r'^qs/',
        'apps.question.views.questions',
        name='questions'),

    url(r'^pq/',
        'apps.account.views.pending_questions',
        name='pending-questions'),

    url(r'^pqa/',
        'apps.question.views.pending_question_action',
        name='pending-question-action'),

    url(r'^n/$',
        'apps.notification.views.notifications',
        name='notifications'),

    url(r'^n/m/$',
        'apps.notification.views.mark_as_read',
        name='mark_notification_as_read'),

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

    url(r'^fq/$',
        'apps.question.views.follow_question',
        name='follow_question'),

    url(r'^hof/$',
        'apps.account.views.hof',
        name='hof'),

    url(r'^test/$',
        TemplateView.as_view(template_name="test.html"),
        name='test'),

    url(r'^api/v1/story/list/public/$', PublicStoryList.as_view(),
        name='api-public-story-list'),

    url(r'^api/v1/story/list/user/(?P<username>[-\w]+)/$',
        UserStoryList.as_view(),
        name='api-user-story-list'),

    url(r'^api/v1/user/list/',
        UserList.as_view(),
        name='api-user-list'),

    url(r'^adminmisinlansen/',
        include(admin.site.urls)),

    url(r'^rosetta/', include('rosetta.urls')),

    url(r'pm/', include('apps.pm.urls')),

    url(r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap', {
        'sitemaps': {
            'qmeta': QMetaSitemap,
            'story': StorySiteMap
        }
    }, name='django.contrib.sitemaps.views.sitemap'),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        '',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT, }),
        url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.STATIC_ROOT, }),
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
