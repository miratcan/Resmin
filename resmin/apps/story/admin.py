from django.contrib import admin
from apps.story.models import (Story, Slot, Image, Upload)


class StoryAdmin(admin.ModelAdmin):
    list_display = ('__unicode__',
                    'is_nsfw',
                    'is_featured',
                    'is_anonymouse',
                    'status',
                    'created_at')


class SlotAdmin(admin.ModelAdmin):
    list_display = ('story', 'order')


class ImageAdmin(admin.ModelAdmin):
    list_display = ('image', 'md5sum')


class UploadAdmin(admin.ModelAdmin):
    list_display = ('upload_id', 'owner', 'status', 'created_at')


admin.site.register(Story, StoryAdmin)
admin.site.register(Slot, SlotAdmin)
admin.site.register(Image, ImageAdmin)
admin.site.register(Upload, UploadAdmin)
