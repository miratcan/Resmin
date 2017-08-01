from django.contrib import admin
from .models import (NotificationMeta, NotificationPreference,
                     NotificationType, NotificationTypeTranslation,
                     SiteNotification, EmailNotification)
from multilingual_model.admin import TranslationStackedInline


class NotificationMetaAdmin(admin.ModelAdmin):
    list_display = ('ntype', 'recipient', 'is_published', 'is_read', 's_pks',
                    'o_pks')


class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'ntype')


class NotificationTypeTranslationInline(TranslationStackedInline):
    model = NotificationTypeTranslation


class NotificationTypeAdmin(admin.ModelAdmin):
    list_display = ('slug', 'is_active', 'plural', 's_ct', 'o_ct')
    inlines = [NotificationTypeTranslationInline]


class EmailNotificationAdmin(admin.ModelAdmin):
    list_display = ('meta', 'recipient_email', 'subject', 'is_sent')


admin.site.register(NotificationMeta, NotificationMetaAdmin)
admin.site.register(SiteNotification)
admin.site.register(EmailNotification, EmailNotificationAdmin)
admin.site.register(NotificationPreference, NotificationPreferenceAdmin)
admin.site.register(NotificationType, NotificationTypeAdmin)
