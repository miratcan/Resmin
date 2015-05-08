from json import dumps

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _

from libs.baseconv import base62

from apps.question.models import QuestionMeta
from apps.moderation.forms import ComplainQuestionMetaForm


def complain_question(request, base62_id):
    qmeta = get_object_or_404(QuestionMeta, id=base62.to_decimal(base62_id))
    complain_form = ComplainQuestionMetaForm(
        qmeta=qmeta)
    descriptions = dumps(ComplainQuestionMetaForm._meta.model.DESCRIPTION_MAP)
    if request.method == "POST":
        complain_form = ComplainQuestionMetaForm(request.POST, qmeta=qmeta)
        if complain_form.is_valid():
            complain_form.save(complainer=request.user)
            messages.success(request, _('Your complaint sent to moderation.'))
            return HttpResponseRedirect(qmeta.get_absolute_url())

    return render(request, 'moderation/complain_qmeta.html', {
        'complain_form': complain_form,
        'descriptions': descriptions})


def _update_question(request, base62_id):
    pass


def _merge_question(request, base62_id):
    pass


def question_moderation(request, base62_id):
    actions = {'update': _update_question, 'merge': _merge_question}
    return render(request, 'moderation/question_moderation.html')
