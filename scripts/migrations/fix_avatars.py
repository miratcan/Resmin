from django.contrib.auth.models import User
from apps.question.models import Answer
from django.conf import settings

for u in User.objects.all():

    try:
        p = u.userprofile
    except:
        continue

    if not u.userprofile.avatar:
        answers = Answer.objects.filter(owner=u, question_id = settings.AVATAR_QUESTION_ID)
        if answers:
            u.userprofile.avatar = answers[0].image
            u.userprofile.save()