from django.contrib import admin
from apps.notification.models import Notification
from apps.notification.models import NotificationPreference
from apps.notification.models import NotificationType


class NotificationAdmin(admin.ModelAdmin):
    list_display = ('actor', 'ntype', 'recipient')


class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'ntype', 'subscription_status')


class NotificationTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')


admin.site.register(Notification, NotificationAdmin)
admin.site.register(NotificationPreference, NotificationPreferenceAdmin)
admin.site.register(NotificationType, NotificationTypeAdmin)
