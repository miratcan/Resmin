from rest_framework import serializers
from .models import Story


class StorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Story
        fields = ('id',
                  'title',
                  'description',
                  'is_nsfw',
                  'is_anonymouse',
                  'is_featured',
                  'like_count',
                  'slot_count',
                  'comment_count',
                  'status',
                  'visible_for',
                  'owner',
                  'question',
                  'question_meta')
