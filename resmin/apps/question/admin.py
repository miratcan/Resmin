from django.contrib import admin
from apps.question.models import QuestionMeta, Question, QuestionMetaComplaint
from apps.story.models import Story


class QuestionMetaAdmin(admin.ModelAdmin):
    list_display = ('text', 'redirected_to', 'created_at', 'updated_at',
                    'answer_count', 'follower_count', 'is_featured', 'status')
    fields = ('text', 'owner', 'status', 'redirected_to',
              'is_featured', 'is_sponsored')
    raw_id_fields = ('redirected_to', 'owner')
    search_fields = ('text',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Override redirected_to queryset to not redirected QuestionMeta
        objects.
        """
        if db_field.name == "redirected_to":
            kwargs["queryset"] = QuestionMeta.objects.filter(
                redirected_to=None)
        return super(QuestionMetaAdmin, self)\
            .formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        redirected_to = form.cleaned_data.get('redirected_to')
        """
        Move stories of source question meta to target questionmeta.
        TODO: Move followers of source question meta to target questionmeta.
        """
        if redirected_to:
            Story.objects.filter(question_meta=obj).update(
                question_meta=redirected_to)
            redirected_to.update_answer_count()
            redirected_to.save(update_fields=['answer_count'])
        return super(QuestionMetaAdmin, self)\
            .save_model(request, obj, form, change)


class QuestionAdmin(admin.ModelAdmin):
    list_display = ('questioner', 'questionee', 'meta')


class QuestionMetaComplaintAdmin(admin.ModelAdmin):
    list_display = ('question_meta', 'complaint_type', 'status')

admin.site.register(Question, QuestionAdmin)
admin.site.register(QuestionMeta, QuestionMetaAdmin)
admin.site.register(QuestionMetaComplaint, QuestionMetaComplaintAdmin)