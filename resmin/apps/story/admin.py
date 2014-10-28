from django.contrib import admin
from apps.story.models import (Story, Slot, Image)

class StoryAdmin(admin.ModelAdmin):
    list_display = ('__unicode__',
                    'is_nsfw',
                    'status',
                    'created_at')

class SlotAdmin(admin.ModelAdmin):
    list_display = ('story', 'order')


class ImageAdmin(admin.ModelAdmin):
    list_display = ('image', 'md5sum')


admin.site.register(Story, StoryAdmin)
admin.site.register(Slot, SlotAdmin)
admin.site.register(Image, ImageAdmin)