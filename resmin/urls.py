from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings

from django.views.generic import TemplateView
from django.contrib.sitemaps import Sitemap
from apps.question.models import QuestionMeta
from apps.story.models import Story
from apps.question import views as question_views
from apps.account import views as account_views
from apps.comment import views as comment_views
from django.contrib.auth import views as auth_views
from apps.story import views as story_views
from apps.notification import views as notification_views

admin.autodiscover()

urlpatterns = [
    url(r'^$',
        question_views.index,
        name='index', kwargs={'listing': 'wall'}),

    url(r'^public/$',
        question_views.index,
        name='index-public', kwargs={'listing': 'public'}),

    url(r'^q/(?P<base62_id>[-\w]+)/complain/$',
        question_views.complain_question,
        name='complain-question'),

    url(r'^q/(?P<base62_id>[-\w]+)/answer/$',
        story_views.create_story,
        name='create-story'),

    url(r'^q/(?P<base62_id>[-\w]+)(?:/(?P<ordering>[a-zA-Z]+))?/$',
        question_views.question,
        name='question'),

    url(r'^q/(?P<base62_id>[-\w]+)/delete/$',
        question_views.question,
        name='delete_question',
        kwargs={'show_delete': True}),

    url(r'^qs/',
        question_views.questions,
        name='questions'),

    url(r'^pq/',
        question_views.pending_questions,
        name='pending-questions'),

    url(r'^pqa/',
        question_views.pending_question_action,
        name='pending-question-action'),

    url(r'^pfr/$',
        account_views.pending_follow_requests,
        name='pending-follow-requests'),

    url(r'^pfra/$',
        account_views.pending_follow_request_action,
        name='pending-follow-request-action'),

    url(r'^u/(?P<username>[-\w]+)/(?P<action>(block|unblock|follow|unfollow))?/?$',
        account_views.profile,
        name='profile'),

    url(r'^u/(?P<username>[-\w]+)/followers/$',
        account_views.followers,
        name='followers'),

    url(r'^u/(?P<username>[-\w]+)/followings/$',
        account_views.followings,
        name='followings'),

    url(r'^u/(?P<username>[-\w]+)/draft/',
        account_views.profile,
        name='profile-drafts',
        kwargs={'listing': 'draft'}),

    url(r'^e/$',
        account_views.email,
        name='email_form'),

    url(r'^e/(?P<key>[-\w]+)/$',
        account_views.email,
        name='email_confirm'),

    url(r'^reg/$',
        account_views.register,
        name='register'),

    url(r'^c/(?P<cid>[-\d]+)/$',
        comment_views.get_comment,
        name='get_comment'),

    url(r'^c/u/(?P<cid>[-\d]+)/$',
        comment_views.update_comment,
        name='update_comment'),

    url(r'^c/d/(?P<cid>[-\d]+)/$',
        comment_views.delete_comment,
        name='delete_comment'),

    url(r'^me/update/$',
        account_views.update_profile,
        name='update_profile'),

    url(r'^me/notification/preferences/$',
        account_views.notification_preferences,
        name='update_notification_preferences'),

    url(r'^p/r/$',
        auth_views.password_reset,
        name='password_reset',
        kwargs={'template_name': 'auth/password_reset_form.html',
                'subject_template_name': 'emails/password_reset_subject.txt',
                'email_template_name': 'emails/password_reset_body.txt'}
        ),

    url(r'^p/r/sent/$',
        auth_views.password_reset_done,
        name='password_reset_sent',
        kwargs={'template_name': 'auth/password_reset_sent.html', }
        ),

    url(r'^p/r/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$',
        auth_views.password_reset_confirm,
        name='password_reset_confirm',
        kwargs={'post_reset_redirect': '/p/r/complete/',
                'template_name': 'auth/password_reset_confirm.html'}),

    url(r'^p/r/done/$',
        auth_views.password_reset_done,
        name='password_reset_done',
        kwargs={'template_name': 'auth/password_reset_done.html'}),

    url(r'^p/r/complete/$',
        auth_views.password_reset_complete,
        name='password_reset_complete',
        kwargs={'template_name': 'auth/password_reset_complete.html'}),

    url(r'^upload/$',
        story_views.get_upload, name='get_upload'),

    url(r'^upload/(?P<upload_id>[-\w]+)/$',
        story_views.upload,
        name='upload'),


    url(r'^s/(?P<base62_id>[-\w]+)/$',
        story_views.story,
        name='story'),

    url(r'^s/(?P<base62_id>[-\w]+)/ui/$',
        story_views.update_story,
        name='update-images-of-story'),

    url(r'^s/(?P<base62_id>[-\w]+)/ud/$',
        story_views.update_details,
        name='update-details-of-story'),

    url(r'^n/$',
        notification_views.notifications,
        name='notifications'),

    url(r'^n/m/$',
        notification_views.mark_as_read,
        name='mark_notification_as_read'),

    url(r'^login/$',
        auth_views.login,
        name='login', kwargs={'template_name': 'auth/login.html'}),

    url(r'^logout/$',
        auth_views.logout,
        name='logout', kwargs={'next_page': '/'}),

    url(r'^i/$',
        account_views.invitations,
        name='invitations'),

    url(r'^l/$',
        question_views.like,
        name='like'),

    url(r'^fq/$',
        question_views.follow_question,
        name='follow_question'),

    url(r'^hof/$',
        account_views.hof,
        name='hof'),

    url(r'^test/$',
        TemplateView.as_view(template_name="test.html"),
        name='test'),

    url(r'^adminmisinlansen/',
        include(admin.site.urls)),

    url(r'pm/', include('apps.pm.urls')),

]

if settings.DEBUG:
    from django.views.static import serve
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),

        url(r'^media/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT, }),
        url(r'^static/(?P<path>.*)$', serve, {
            'document_root': settings.STATIC_ROOT, }),
    ]
