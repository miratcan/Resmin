from django.contrib import admin
from apps.follow.models import UserFollow

class UserFollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'target', 'status')

admin.site.register(UserFollow, UserFollowAdmin)
