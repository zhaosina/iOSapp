
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import SpeakingQuestion, PracticeRecord, DailyPlan

class SpeakingQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpeakingQuestion
        fields = ['id', 'task_type', 'prompt_text', 'sample_answer', 'created_at']


class PracticeRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = PracticeRecord
        fields = [
            'id',
            'user',               # 用户 ID
            'question',           # 题目 ID
            'audio_url',
            'text_answer',
            'overall_score',
            'pronunciation_score',
            'fluency_score',
            'vocabulary_score',
            'coherence_score',
            'feedback_json',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'overall_score', 'pronunciation_score', 'fluency_score',
            'vocabulary_score', 'coherence_score', 'feedback_json',
            'created_at', 'updated_at'
        ]


class DailyPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyPlan
        fields = ['id', 'user', 'plan_date', 'tasks_json', 'created_at']
        read_only_fields = ['created_at']
