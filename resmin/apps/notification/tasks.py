from resmin.celery_app import app
from apps.notification.models import NotificationMeta


@app.task
def publish_notifications():
    for nm in NotificationMeta.objects.filter(is_published=False):
        nm.publish()
