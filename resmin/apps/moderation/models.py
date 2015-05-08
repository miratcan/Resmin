from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext as _
from apps.question.models import QuestionMeta


class QuestionMetaComplaint(models.Model):

    DUPLICATE = 0
    MEANINGLESS = 1
    HATE_SPEECH = 2
    INSULTING = 3

    PENDING = 0
    SOLVED = 1
    REJECTED = 2

    DESCRIPTION_MAP = {
        DUPLICATE: _(
            'If you think that there is a question already has '
            'meaning of given question, type URL of other question.'),
        MEANINGLESS: _(
            'If question is something like: \'fddskfllksd\' use '
            'this one.'),
        HATE_SPEECH: _(
            'If question is targeting spesific audience with hate '
            'use this one. Write some explanation to make admins understand '
            'situation.'),
        INSULTING: _(
            'If question is insulting you or your life us this one.'
            'Write some explanation to make admins understand situation.')}

    question_meta = models.ForeignKey(QuestionMeta)
    complain_type = models.PositiveIntegerField(
        choices=((DUPLICATE, _('Duplicate')), (MEANINGLESS, _('Meaningless')),
                 (HATE_SPEECH, _('Hate Speech')), (INSULTING, _('Insulting'))))
    status = models.PositiveIntegerField(
        default=PENDING, choices=((PENDING, _('Pending')),
                                  (SOLVED, _('Solved')),
                                  (REJECTED, _('Rejected'))))
    complainers = models.ManyToManyField(User)
    description = models.TextField(null=True, blank=True)

    def action_delete(self):
        pass

    def action_merge(self, target_qm):
        pass
