from django.contrib import admin
from apps.notification.models import (NotificationMeta, NotificationPreference,
                                      NotificationType, SiteNotification,
                                      EmailNotification)


class NotificationMetaAdmin(admin.ModelAdmin):
    list_display = ('ntype', 'recipient', 'is_published', 's_pks', 'o_pks')


class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'ntype')


class NotificationTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'plural', 's_ct', 'o_ct')


admin.site.register(NotificationMeta, NotificationMetaAdmin)
admin.site.register(SiteNotification)
admin.site.register(EmailNotification)
admin.site.register(NotificationPreference, NotificationPreferenceAdmin)
admin.site.register(NotificationType, NotificationTypeAdmin)
