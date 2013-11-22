from django.contrib import admin
from apps.follow.models import UserFollow, QuestionFollow


class UserFollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'target', 'status')


class QuestionFollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'target', 'reason')

admin.site.register(UserFollow, UserFollowAdmin)
admin.site.register(QuestionFollow, QuestionFollowAdmin)
