# api/admin.py

from django.contrib import admin
from .models import SpeakingQuestion, PracticeRecord, DailyPlan

@admin.register(SpeakingQuestion)
class SpeakingQuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'task_type', 'prompt_text', 'created_at')
    list_filter = ('task_type',)
    search_fields = ('prompt_text',)
    ordering = ('-created_at',)


@admin.register(PracticeRecord)
class PracticeRecordAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'question', 'overall_score', 'pronunciation_score',
        'fluency_score', 'vocabulary_score', 'coherence_score', 'created_at'
    )
    list_filter = ('question__task_type', 'created_at')
    search_fields = ('user__username', 'question__prompt_text')
    ordering = ('-created_at',)
    readonly_fields = ('overall_score', 'pronunciation_score', 'fluency_score', 'vocabulary_score', 'coherence_score')


@admin.register(DailyPlan)
class DailyPlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'plan_date', 'created_at')
    list_filter = ('plan_date',)
    search_fields = ('user__username',)
    ordering = ('-plan_date',)
