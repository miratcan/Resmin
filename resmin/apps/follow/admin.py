from django.contrib import admin
from apps.follow.models import UserFollow, QuestionFollow, StoryFollow


class UserFollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'target', 'status')


class QuestionFollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'target', 'reason', 'status')

admin.site.register(UserFollow, UserFollowAdmin)
admin.site.register(QuestionFollow, QuestionFollowAdmin)
admin.site.register(StoryFollow)
