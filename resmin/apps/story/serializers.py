from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Story


class UserSerializer(serializers.ModelSerializer):

    bio = serializers.CharField(
        source='profile.bio', read_only=True)

    follower_count = serializers.IntegerField(
        source='profile.follower_count', read_only=True)

    following_count = serializers.IntegerField(
        source='profile.following_count', read_only=True)

    story_count = serializers.IntegerField(
        source='profile.story_count', read_only=True)

    avatar = serializers.CharField(
        source='profile.avatar', read_only=True)

    class Meta:
        model = User
        fields = ('username',
                  'bio',
                  'following_count',
                  'follower_count',
                  'story_count',
                  'avatar')


class JSONSerializerField(serializers.Field):
    """ Serializer for JSONField -- required to make field writable. """

    def to_internal_value(self, data):
        return data

    def to_representation(self, value):
        return value


class StorySerializer(serializers.ModelSerializer):

    question_meta_text = serializers.CharField(
        source='question_meta.text', read_only=True)

    owner = serializers.CharField(
        source='owner.username', read_only=True)

    cover_img = JSONSerializerField(
        read_only=True)

    class Meta:
        model = Story
        fields = ('id',
                  'title',
                  'description',
                  'is_nsfw',
                  'is_featured',
                  'like_count',
                  'slot_count',
                  'comment_count',
                  'cover_img',
                  'status',
                  'owner',
                  'question',
                  'question_meta',
                  'question_meta_text')
