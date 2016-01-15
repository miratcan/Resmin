from django.contrib import admin
from apps.story.models import (Story, Slot, Image, Video, Upload)


class StoryAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'question_meta', 'is_nsfw', 'is_featured',
                    'status', 'created_at')
    fields = ('owner', 'question_meta', 'title', 'description', 'status',
              'cover_img')
    search_fields = ('title', 'description', 'question_meta__text')


class SlotAdmin(admin.ModelAdmin):
    list_display = ('story', 'order')


class ImageAdmin(admin.ModelAdmin):
    list_display = ('image', 'md5sum')


class VideoAdmin(admin.ModelAdmin):
    list_display = ('video', 'md5sum')


class UploadAdmin(admin.ModelAdmin):
    list_display = ('upload_id', 'owner', 'status', 'created_at')


admin.site.register(Story, StoryAdmin)
admin.site.register(Slot, SlotAdmin)
admin.site.register(Image, ImageAdmin)
admin.site.register(Video, VideoAdmin)
admin.site.register(Upload, UploadAdmin)
