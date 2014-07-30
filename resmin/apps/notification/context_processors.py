from apps.follow.models import UserFollow
from apps.question.models import AnswerRequest
from apps.notification.models import Notification


def notifications(request):

    if not request.user.is_authenticated():
        return {}

    pfr = UserFollow.objects.filter(
        target=request.user, status=0).count()
    par = AnswerRequest.objects.filter(
        questionee=request.user, status=0).count()
    pns = Notification.objects.filter(
        recipient=request.user).count()

    return {'num_of_pending_follow_requests': pfr,
            'num_of_pending_answer_requests': par,
            'num_of_pending_notifications': pns}
