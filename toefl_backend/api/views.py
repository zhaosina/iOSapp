# api/views.py

import os
from rest_framework import generics, status, permissions, parsers
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from django.core.paginator import Paginator
from .models import SpeakingQuestion, PracticeRecord, DailyPlan
from .serializers import (
    SpeakingQuestionSerializer,
    PracticeRecordSerializer,
    DailyPlanSerializer
)
from .qwen_client import call_qwen_omni_audio_diagnosis, QwenClientError


# ------------------------------------------
# 1. 题库查询接口
# ------------------------------------------

class QuestionListAPIView(generics.ListAPIView):
    """
    GET /api/v1/questions/?task_type=1&page=1&page_size=10
    返回分页后的题目列表。
    """
    serializer_class = SpeakingQuestionSerializer
    permission_classes = [permissions.AllowAny]  # 可根据需求改成 IsAuthenticated

    def get_queryset(self):
        qs = SpeakingQuestion.objects.all().order_by('-created_at')
        task_type = self.request.query_params.get('task_type')
        if task_type in ('1', '2'):
            qs = qs.filter(task_type=int(task_type))
        return qs

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        # 分页逻辑
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        serializer = self.get_serializer(page_obj, many=True)
        return Response({
            "count": paginator.count,
            "total_pages": paginator.num_pages,
            "current_page": page,
            "results": serializer.data
        })


class QuestionDetailAPIView(generics.RetrieveAPIView):
    """
    GET /api/v1/questions/<id>/
    获取单个题目详情
    """
    queryset = SpeakingQuestion.objects.all()
    serializer_class = SpeakingQuestionSerializer
    permission_classes = [permissions.AllowAny]


# ------------------------------------------
# 2. 提交作答并调用 Qwen2.5-Omni 评分接口
# ------------------------------------------

class PracticeAudioDiagnosisAPIView(APIView):
    """
    POST /api/v1/practice/audio_diagnosis/
    使用 multipart/form-data 上传字段：
      - question_id: int
      - audio_file: 文件，wav/m4a/mp3 等
    返回：Qwen-Omni 诊断结果 JSON
    """
    parser_classes = [parsers.MultiPartParser]
    permission_classes = [permissions.IsAuthenticated]  # 需登录

    def post(self, request, *args, **kwargs):
        user = request.user
        question_id = request.data.get("question_id")
        audio_file = request.FILES.get("audio_file")

        if not question_id or not audio_file:
            return Response({"detail": "缺少 question_id 或 audio_file"},
                            status=status.HTTP_400_BAD_REQUEST)

        # 1. 将上传的音频保存到 media/practice_audio/
        save_dir = os.path.join(settings.MEDIA_ROOT, "practice_audio")
        os.makedirs(save_dir, exist_ok=True)
        filename = f"user{user.id}_q{question_id}_{audio_file.name}"
        file_path = os.path.join(save_dir, filename)
        with open(file_path, "wb") as f:
            for chunk in audio_file.chunks():
                f.write(chunk)

        # 2. 调用 Qwen2.5-Omni API 端到端评分
        try:
            diagnosis = call_qwen_omni_audio_diagnosis(file_path)
        except QwenClientError as e:
            return Response({"detail": "Qwen2.5-Omni 调用失败", "error": str(e)},
                            status=status.HTTP_502_BAD_GATEWAY)

        # 3. 保存 PracticeRecord 到数据库
        try:
            question = SpeakingQuestion.objects.get(pk=question_id)
        except SpeakingQuestion.DoesNotExist:
            return Response({"detail": "题目不存在"}, status=status.HTTP_404_NOT_FOUND)

        # 从 diagnosis 取出各维度分数与反馈
        overall = diagnosis.get("overall_score")
        scores = diagnosis.get("scores", {})
        feedback = diagnosis.get("feedback", {})

        record = PracticeRecord.objects.create(
            user=user,
            question=question,
            audio_url=os.path.join("practice_audio", filename),
            text_answer=None,  # 纯音频场景
            overall_score=overall,
            pronunciation_score=scores.get("pronunciation"),
            fluency_score=scores.get("fluency"),
            vocabulary_score=scores.get("vocabulary"),
            coherence_score=scores.get("coherence"),
            feedback_json=feedback
        )

        # 4. 返回诊断结果
        return Response({
            "record_id": record.id,
            "overall_score": overall,
            "scores": scores,
            "feedback": feedback
        }, status=status.HTTP_201_CREATED)


# ------------------------------------------
# 3. 查询作答历史接口
# ------------------------------------------

class PracticeHistoryAPIView(APIView):
    """
    GET /api/v1/practice/history/?user_id=<user_id>&page=&page_size=
    返回指定用户的练习历史（分页）
    """
    permission_classes = [permissions.IsAuthenticated]  # 需登录

    def get(self, request, *args, **kwargs):
        user_id = request.query_params.get("user_id")
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 10))

        if not user_id:
            return Response({"detail": "缺少 user_id"}, status=status.HTTP_400_BAD_REQUEST)

        if int(user_id) != request.user.id:
            return Response({"detail": "无权查看其他用户记录"}, status=status.HTTP_403_FORBIDDEN)

        records = PracticeRecord.objects.filter(user_id=user_id).order_by('-created_at')
        paginator = Paginator(records, page_size)
        page_obj = paginator.get_page(page)
        serializer = PracticeRecordSerializer(page_obj, many=True)
        return Response({
            "count": paginator.count,
            "total_pages": paginator.num_pages,
            "current_page": page,
            "results": serializer.data
        })


# ------------------------------------------
# 4. 查询每日计划接口
# ------------------------------------------

class DailyPlanTodayAPIView(APIView):
    """
    GET /api/v1/plans/today/?user_id=<user_id>&date=YYYY-MM-DD
    返回指定用户指定日期的 DailyPlan（如不存在，可返回空或创建默认空计划）
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user_id = request.query_params.get("user_id")
        plan_date = request.query_params.get("date")
        if not user_id or not plan_date:
            return Response({"detail": "缺少 user_id 或 date 参数"}, status=status.HTTP_400_BAD_REQUEST)

        if int(user_id) != request.user.id:
            return Response({"detail": "无权查看其他用户的计划"}, status=status.HTTP_403_FORBIDDEN)

        try:
            plan = DailyPlan.objects.get(user_id=user_id, plan_date=plan_date)
        except DailyPlan.DoesNotExist:
            # 如果不存在，返回空数据（也可选择自动创建）
            return Response({"detail": "当日计划不存在", "tasks": []}, status=status.HTTP_200_OK)

        serializer = DailyPlanSerializer(plan)
        return Response(serializer.data, status=status.HTTP_200_OK)
