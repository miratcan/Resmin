from apps.follow.models import UserFollow
from apps.question.models import Question
from apps.notification.models import SiteNotification


def notifications(request):

    if not request.user.is_authenticated():
        return {}

    pfr = UserFollow.objects.filter(
        target=request.user, status=0).count()
    pqs = Question.objects.filter(
        questionee=request.user, status=0).count()
    pns = SiteNotification.objects.filter(
        meta__recipient=request.user, meta__is_read=False).count()

    return {'num_of_pending_follow_requests': pfr,
            'num_of_pending_questions': pqs,
            'num_of_pending_notifications': pns}
