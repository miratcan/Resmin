from ..follow.models import UserFollow
from ..question.models import Question
from ..pm.models import Message
from .models import SiteNotification


def notifications(request):

    if not request.user.is_authenticated():
        return {}

    pfr = UserFollow.objects.filter(
        target=request.user, status=0).count()
    pqs = Question.objects.filter(
        questionee=request.user, status=0).count()
    pns = SiteNotification.objects.filter(
        meta__recipient=request.user, meta__is_read=False).count()
    um = Message.objects.filter(recipient=request.user, read_at__isnull=True,
                                recipient_deleted_at__isnull=True).count()

    return {'num_of_pending_follow_requests': pfr,
            'num_of_pending_questions': pqs,
            'num_of_pending_notifications': pns,
            'num_of_unread_messages': um}
