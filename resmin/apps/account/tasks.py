from resmin.celery_app import app

@app.task
def follower_count_changed_callback_task(user):
    profile = user.get_profile()
    profile.update_follower_count()
    profile.save(update_fields=['follower_count'])
