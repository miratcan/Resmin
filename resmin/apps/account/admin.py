from django.contrib import admin
from apps.account.models import Invitation, UserProfile, EmailCandidate


class EmailCandidateAdmin(admin.ModelAdmin):
    list_display = ('email', 'key')


class InvitationAdmin(admin.ModelAdmin):
    list_display = ('key', 'owner', 'used_count')


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio', 'like_count', 'story_count',
                    'follower_count')
    search_fields = ['user']

admin.site.register(Invitation, InvitationAdmin)
admin.site.register(UserProfile, ProfileAdmin)
admin.site.register(EmailCandidate, EmailCandidateAdmin)
