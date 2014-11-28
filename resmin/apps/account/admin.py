from django.contrib import admin
from apps.account.models import Invitation, UserProfile, EmailCandidate


class InvitationAdmin(admin.ModelAdmin):
    list_display = ('key', 'owner', 'used_by')


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio', 'like_count', 'story_count',
                    'follower_count')

admin.site.register(Invitation, InvitationAdmin)
admin.site.register(UserProfile, ProfileAdmin)
admin.site.register(EmailCandidate)
