from factory import DjangoModelFactory, SubFactory
from factory import Sequence, PostGenerationMethodCall

DEFAULT_USER_PASSWORD = '1'


class UserFactory(DjangoModelFactory):
    username = Sequence(lambda n: "usr_%03d" % n)
    email = Sequence(lambda n: "email%03d@address.com" % n)
    password = PostGenerationMethodCall('set_password', DEFAULT_USER_PASSWORD)
    is_active = True

    class Meta:
        model = 'auth.User'


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


class QuestionMetaFactory(DjangoModelFactory):
    class Meta:
        model = 'question.QuestionMeta'


class StoryFactory(DjangoModelFactory):
    class Meta:
        model = 'story.Story'


class NotificationTypeFactory(DjangoModelFactory):
    class Meta:
        model = 'notification.NotificationType'


class CommentFactory(DjangoModelFactory):
    class Meta:
        model = 'comment.Comment'
