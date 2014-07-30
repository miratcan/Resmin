from django.contrib import admin
from apps.question.models import Question, Answer, AnswerRequest


def merge_questions(modeladmin, request, queryset):
    question_to_merge = queryset.order_by("created_at")[0]
    questions_will_merged = queryset.exclude(id=question_to_merge.id)

    for question in questions_will_merged:
        question.answer_set.all().update(question=question_to_merge)
        question.merged_to = question_to_merge
        question.save()

merge_questions.short_description = "Merge selected questions to oldest"


class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text',
                    'owner',
                    'created_at',
                    'updated_at',
                    'is_featured',)

    actions = [merge_questions]


class AnswerAdmin(admin.ModelAdmin):
    list_display = ('question',
                    'owner',
                    'image',
                    'is_nsfw',
                    'status',
                    'created_at')


admin.site.register(Question, QuestionAdmin)
admin.site.register(Answer, AnswerAdmin)
admin.site.register(AnswerRequest)