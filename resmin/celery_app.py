from __future__ import absolute_import
from os import environ
from celery import Celery

environ.setdefault('DJANGO_SETTINGS_MODULE', 'resmin.config.settings')

from django.conf import settings

# Create celery app instance
app = Celery('resmin')

# Configure app from django settings
app.config_from_object('django.conf:settings')


# Autodiscover tasks
app.autodiscover_tasks(settings.INSTALLED_APPS, related_name='tasks')


# Here is a dummy task to test if celery is running
@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
