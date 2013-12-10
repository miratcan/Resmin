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

