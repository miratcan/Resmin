from django.contrib import admin
from apps.notification.models import (NotificationMeta, NotificationPreference,
                                      NotificationType, SiteNotification,
                                      EmailNotification)


class NotificationMetaAdmin(admin.ModelAdmin):
    list_display = ('ntype', 'recipient', 'is_published', 's_tp', 's_pks',
                    'o_tp', 'o_pks')


class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'ntype')


class NotificationTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'plural')


admin.site.register(NotificationMeta, NotificationMetaAdmin)
admin.site.register(SiteNotification)
admin.site.register(EmailNotification)
admin.site.register(NotificationPreference, NotificationPreferenceAdmin)
admin.site.register(NotificationType, NotificationTypeAdmin)
