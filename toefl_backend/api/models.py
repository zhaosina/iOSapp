# api/models.py

from django.db import models
from django.contrib.auth.models import User

class SpeakingQuestion(models.Model):
    """
    托福口语题库表
    """
    TASK_CHOICES = (
        (1, "Task1"),
        (2, "Task2"),
    )
    task_type = models.PositiveSmallIntegerField(choices=TASK_CHOICES, verbose_name="题目类型")
    prompt_text = models.CharField(max_length=2000, verbose_name="题干文本")
    sample_answer = models.TextField(blank=True, null=True, verbose_name="示范答案")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = "api_speakingquestion"
        indexes = [
            models.Index(fields=["task_type"], name="idx_task_type"),
        ]
        verbose_name = "托福口语题目"
        verbose_name_plural = "托福口语题目"

    def __str__(self):
        return f"Task{self.task_type} - {self.prompt_text[:30]}…"


class PracticeRecord(models.Model):
    """
    用户练习记录表，记录用户上传音频或文本答案及 Qwen-Omni 评分结果
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    question = models.ForeignKey(SpeakingQuestion, on_delete=models.CASCADE, verbose_name="题目")
    audio_url = models.CharField(max_length=500, blank=True, null=True, verbose_name="音频文件相对路径")
    text_answer = models.TextField(blank=True, null=True, verbose_name="文本答案")
    overall_score = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True, verbose_name="总评分")
    pronunciation_score = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True, verbose_name="发音评分")
    fluency_score = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True, verbose_name="流利度评分")
    vocabulary_score = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True, verbose_name="词汇评分")
    coherence_score = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True, verbose_name="逻辑评分")
    feedback_json = models.JSONField(blank=True, null=True, verbose_name="Qwen 返回的反馈 JSON")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "api_practicerecord"
        indexes = [
            models.Index(fields=["user", "created_at"], name="idx_user_created_at"),
        ]
        verbose_name = "练习记录"
        verbose_name_plural = "练习记录"

    def __str__(self):
        return f"{self.user.username} - Q{self.question.id} @ {self.created_at:%Y-%m-%d %H:%M}"


class DailyPlan(models.Model):
    """
    用户每日专项练习计划表
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    plan_date = models.DateField(verbose_name="计划日期")
    tasks_json = models.JSONField(verbose_name="当日专项练习题目列表与维度")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = "api_dailyplan"
        unique_together = (("user", "plan_date"),)
        verbose_name = "每日专项计划"
        verbose_name_plural = "每日专项计划"

    def __str__(self):
        return f"{self.user.username} - {self.plan_date}"
