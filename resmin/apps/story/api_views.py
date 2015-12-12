from django.contrib.auth.models import User
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.response import Response
from resmin.apps.story.serializers import StorySerializer
from resmin.apps.story.models import Story
from resmin.apps.story.serializers import UserSerializer


class BaseStoryList(generics.ListAPIView):
    model = Story
    serializer_class = StorySerializer
    paginate_by = settings.STORIES_PER_PAGE

class PublicStoryList(BaseStoryList):
    queryset = Story.objects.build(listing='public')

class UserStoryList(BaseStoryList):
    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs['username'])
        return Story.objects.build(listing='public', frm=user)


    def list(self, request, *args, **kwargs):
        instance = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(instance)
        if page is not None:
            serializer = self.get_pagination_serializer(page)
        else:
            serializer = self.get_serializer(instance, many=True)
        data = serializer.data
        user = User.objects.get(username=kwargs['username'])
        data.update({'user': UserSerializer(user).data})
        return Response(data)


class UserList(generics.ListAPIView):
    model = User
    serializer_class = UserSerializer
    paginate_by = settings.STORIES_PER_PAGE
    queryset = User.objects.filter(is_active=True)