from django.contrib import admin
from apps.question.models import QuestionMeta, Question, QuestionMetaComplaint
from apps.story.models import Story


def merge_questions(modeladmin, request, queryset):
    question_to_merge = queryset.order_by("created_at")[0]
    questions_will_merged = queryset.exclude(id=question_to_merge.id)

    for question in questions_will_merged:
        question.answer_set.all().update(question=question_to_merge)
        question.merged_to = question_to_merge
        question.save()


class QuestionMetaAdmin(admin.ModelAdmin):
    list_display = ('text', 'redirected_to', 'created_at', 'updated_at',
                    'answer_count', 'follower_count', 'is_featured', 'status')
    fields = ('text', 'status', 'redirected_to',
              'is_featured', 'is_sponsored')
    raw_id_fields = ('redirected_to',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "redirected_to":
            kwargs["queryset"] = QuestionMeta.objects.filter(
                redirected_to=None)
        return super(QuestionMetaAdmin, self)\
            .formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        redirected_to = form.cleaned_data.get('redirected_to')
        if redirected_to:
            source = obj
            target = redirected_to
            Story.objects.filter(question_meta=source).update(
                question_meta=target)
        return super(QuestionMetaAdmin, self)\
            .save_model(request, obj, form, change)


class QuestionAdmin(admin.ModelAdmin):
    list_display = ('questioner',
                    'questionee',
                    'meta')

    actions = [merge_questions]


admin.site.register(Question, QuestionAdmin)
admin.site.register(QuestionMeta, QuestionMetaAdmin)
admin.site.register(QuestionMetaComplaint)