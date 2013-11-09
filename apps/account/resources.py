from django.contrib.auth.models import User
from apps.account.models import UserProfile
from tastypie import fields
from tastypie.resources import ModelResource

from tastypie.authentication import ApiKeyAuthentication
from tastypie.authorization import ReadOnlyAuthorization

class ProfileResource(ModelResource):

    class Meta:
        queryset = UserProfile.objects.all()
        resource_name = 'profile'
        list_allowed_methods = []
        detail_allowed_methods = ['get']

        authorization = ReadOnlyAuthorization()
        authentication = ApiKeyAuthentication()



class UserResource(ModelResource):

    profile = fields.ToOneField(ProfileResource, 'profile')

    class Meta:
        queryset = User.objects.all()
        fields = ['username']
        detail_uri_name = 'username'

        authorization = ReadOnlyAuthorization()
        authentication = ApiKeyAuthentication()
