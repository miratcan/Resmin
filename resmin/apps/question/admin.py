from django.contrib import admin
from apps.question.models import QuestionMeta, Question


def merge_questions(modeladmin, request, queryset):
    question_to_merge = queryset.order_by("created_at")[0]
    questions_will_merged = queryset.exclude(id=question_to_merge.id)

    for question in questions_will_merged:
        question.answer_set.all().update(question=question_to_merge)
        question.merged_to = question_to_merge
        question.save()

merge_questions.short_description = "Merge selected questions to oldest"


class QuestionMetaAdmin(admin.ModelAdmin):
    list_display = ('text',
                    'owner',
                    'created_at',
                    'updated_at',
                    'is_featured',)

    actions = [merge_questions]


class QuestionAdmin(admin.ModelAdmin):
    list_display = ('questioner',
                    'questionee',
                    'meta')

    actions = [merge_questions]


admin.site.register(Question, QuestionAdmin)
admin.site.register(QuestionMeta, QuestionMetaAdmin)
