'''
class UserPreferenceSet(models.Model):
    """
    Holds user preferences on relational database. To keep column names clean
    i've shorten field names as:

    ew..: email when
    aa..: an answer
    aq..: a question
    ma..: my answer
    ca..: commented answer

    ew_liked_a........: email when liked answer
    ew_contributed_q..: email when contributed question
    """

    user = models.OneToOneField(User)

    ew_follow_received = models.BooleanField(
        _("Email when somebody sends follow request to me"),
        default=True)

    ew_follow_accepted = models.BooleanField(
        _("Email when my follow request accepted"),
        default=True)

    ew_liked_ma = models.BooleanField(
        _("Email when somebody liked my answer"),
        default=False)

    ew_answered_mq = models.BooleanField(
        _("Email when somebody posted answer to my question"),
        default=True)

    ew_contributed_aq = models.BooleanField(
        _("Email when somebody posted answer to a question that "
          "i contributed"),
        default=True)

    ew_commented_ma = models.BooleanField(
        _("Email when somebody commented on my answer"),
        default=True)

    ew_commented_ca = models.BooleanField(
        _("Email when somebody commented on answer that i commented before"),
        default=True)
'''
