class UserPreferenceSetForm(forms.ModelForm):
    class Meta:
        model = UserPreferenceSet
        fields = ['ew_liked_ma',
                  'ew_answered_mq',
                  'ew_contributed_aq',
                  'ew_commented_ma',
                  'ew_commented_ca']
