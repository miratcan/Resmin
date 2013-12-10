from django.contrib.auth.models import User

from tastypie import fields
from sorl.thumbnail import get_thumbnail

from tastypie.resources import ModelResource
from tastypie.authentication import ApiKeyAuthentication
from tastypie.authorization import ReadOnlyAuthorization

from apps.question.models import Question, Answer
from apps.account.models import UserProfile


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


class QuestionResource(ModelResource):
    """
        Returns questions with number of answer
    """

    latest_answers = fields.ToManyField(
        'apps.question.resources.AnswerResource',
        attribute=lambda b: Answer.objects.filter(question=b.obj)[:4],
        null=True, full=True, use_in='list')

    owner = fields.ToOneField(
        UserResource, 'owner',
        use_in=lambda bundle: not bundle.obj.is_anonymouse)

    class Meta:
        queryset = Question.objects.all()
        resource_name = 'question'
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']

        authorization = ReadOnlyAuthorization()
        authentication = ApiKeyAuthentication()


class AnswerResource(ModelResource):
    question = fields.ToOneField(QuestionResource, 'question')

    owner = fields.ToOneField(
        UserResource, 'owner',
        use_in=lambda bundle: not bundle.obj.is_anonymouse)

    def dehydrate(self, bundle):
        bundle.data['thumbnail'] = get_thumbnail(
            self.instance.image, "172x172", crop="center").url

        bundle.data['image'] = get_thumbnail(
            self.instance.image, "500", crop="center").url

        return bundle

    class Meta:
        queryset = Answer.objects.all()
        resource_name = 'answer'
        list_allowed_methods = []
        detail_allowed_methods = ['get']
        exclude = ['image', 'note']

        authorization = ReadOnlyAuthorization()
        authentication = ApiKeyAuthentication()
