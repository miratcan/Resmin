'''
This file has views that can be used in future.
'''

@csrf_exempt
def follow_answer(request):
    if not request.user.is_authenticated():
        return HttpResponse(status=401)

    # TODO: Make it decorator
    if not request.POST:
        return HttpResponse(status=400)

    aid, act = request.POST.get('qid'), request.POST.get('a')

    if not aid:
        return HttpResponse(status=400)

    if act not in ['follow', 'unfollow']:
        return HttpResponse(status=400)

    answer = get_object_or_404(Answer, id=int(aid))

    if act == 'follow':
        af = AnswerFollow.objects.get_or_create(follower=request.user,
                                                target=answer)[0]

        if not af.status == 0:
            af.reason = 'followed'
            af.status = 0
            af.save(update_fields=['reason', 'status'])

        is_following = True

    elif act == 'unfollow':

        try:
            af = AnswerFollow.objects.get(id=aid)
        except:
            af = None

        if af:
            af.status = 1
            af.save(update_fields=['status'])

        is_following = False

    return HttpResponse(simplejson.dumps({'is_following': is_following}))


@login_required
def update_preferences(request):
    p_set = UserPreferenceSet.objects.get_or_create(user=request.user)[0]
    p_form = UserPreferenceSetForm(instance=p_set)
    if request.method == 'POST':
        p_form = UserPreferenceSetForm(request.POST, instance=p_set)
        if p_form.is_valid():
            p_set = p_form.save()
            messages.success(request, _('Your preferences updated'))
            return HttpResponseRedirect(
                reverse('profile', args=[request.user.username]))
    return render(
        request,
        'auth/preferences.html',
        {'preferences_form': p_form, 'profile_user': request.user})
