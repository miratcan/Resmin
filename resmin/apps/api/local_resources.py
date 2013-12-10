from tastypie.resources import ModelResource

from tastypie.authentication import SessionAuthentication
from tastypie.authorization import Authorization

from apps.follow.models import (QuestionFollow)


class BaseSiteResource(ModelResource):
    class Meta:
        authorization = Authorization()
        authentication = SessionAuthentication()


class QuestionFollow(BaseSiteResource):
    class Meta:
        queryset = QuestionFollow.objects.all()
