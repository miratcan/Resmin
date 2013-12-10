from resources import QuestionResource, UserResource
from tastypie.api import Api

v1_api = Api(api_name='v1')
v1_api.register(QuestionResource())
v1_api.register(UserResource())
