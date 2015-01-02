from datetime import datetime
from datetime import timedelta
from resmin.celery_app import app
from apps.notification.models import NotificationMeta


def _publish_notifications():
    nms = NotificationMeta.objects\
        .prefetch_related('ntype')\
        .filter(is_published=False)
    for nm in nms:
        age = datetime.now() - nm.created_at
        lifespan = timedelta(nm.ntype.collecting_period)
        print age, lifespan
        if age > lifespan:
            print "published."
            nm.publish()


@app.task
def publish_notifications():
    _publish_notifications()
