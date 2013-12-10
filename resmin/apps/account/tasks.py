from resmin.celery_app import app


@app.task
def follow_request_sent_callback_task(target_user):
    preference_set = target_user.preference_set
    if preference_set.ew_follow_received:
        pass


@app.task
def follower_count_changed_callback_task(user):
    profile = user.profile
    profile.update_follower_count()
    profile.save(update_fields=['follower_count'])


@app.task
def following_count_changed_callback_task(user):
    profile = user.profile
    profile.update_following_count()
    profile.save(update_fields=['following_count'])
