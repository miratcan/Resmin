from rest_framework import generics
from apps.story.serializers import StorySerializer
from apps.story.models import Story


class PublicStoryList(generics.ListAPIView):
    model = Story
    serializer_class = StorySerializer
    queryset = Story.objects.build(listing='public')
    paginate_by = 100
