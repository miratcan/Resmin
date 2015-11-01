from factory import DjangoModelFactory
from factory import Sequence, PostGenerationMethodCall,

DEFAULT_USER_PASSWORD = '1'


class UserFactory(DjangoModelFactory):
    email = Sequence(lambda n: "email%03d@address.com" % n)
    password = PostGenerationMethodCall('set_password', DEFAULT_USER_PASSWORD)
    is_active = True

    class Meta:
        model = 'accounts.User'


class UserProfileFactory(DjangoModelFactory):
    class Meta:
        model = 'accounts.UserProfile'


class UserFollowFactory(DjangoModelFactory):
    class Meta:
        model = 'follow.UserFollow'


class QuestionFollowFactory(DjangoModelFactory):
    class Meta:
        model = 'follow.QuestionFollow'


class StoryFollowFactory(DjangoModelFactory):
    class Meta:
        model = 'follow.StoryFollow'


class SlotFactory(DjangoModelFactory):
    class Meta:
        model = 'story.Slot'


class StoryFactory(DjangoModelFactory):
    class Meta:
        model = 'story.Story'
