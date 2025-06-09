# api/utils/qwen_client.py

import base64
import json
import requests
from django.conf import settings

class QwenClientError(Exception):
    pass

def call_qwen_omni_audio_diagnosis(audio_file_path: str) -> dict:
    """
    将音频文件 base64 化，调用 Qwen2.5-Omni API 端到端生成诊断报告。
    返回解析后的 JSON 字典格式：{
        "overall_score": float,
        "scores": {...},
        "feedback": {...}
    }
    """
    # 1. 读取文件并做 base64
    try:
        with open(audio_file_path, "rb") as f:
            audio_bytes = f.read()
    except FileNotFoundError:
        raise QwenClientError(f"音频文件不存在：{audio_file_path}")

    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

    # 2. 构造 System Prompt
    system_content = (
        "你是一个托福口语评分专家。接下来会给你一段学生朗读音频，请分别从 发音(pronunciation)、流利度(fluency)、"
        "词汇(vocabulary)、逻辑结构(coherence) 四个维度打分(0-30)，并给出相应诊断建议。"
        "请按照 JSON 格式返回："
        "{"
        "  \"overall_score\": number,"
        "  \"scores\": {"
        "    \"pronunciation\": number,"
        "    \"fluency\": number,"
        "    \"vocabulary\": number,"
        "    \"coherence\": number"
        "  },"
        "  \"feedback\": {"
        "    \"pronunciation_advice\": string,"
        "    \"fluency_advice\": string,"
        "    \"vocabulary_advice\": string,"
        "    \"coherence_advice\": string"
        "  }"
        "}"
    )

    # 3. 构造请求体
    payload = {
        "model": "Qwen2.5-Omni-7B",
        "modalities": ["text", "audio"],
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": audio_b64}
        ],
        "stream": False
    }

    # 4. 构造鉴权 Header
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.QWEN_ACCESS_KEY_ID}:{settings.QWEN_ACCESS_KEY_SECRET}"
    }

    # 5. 发送请求
    try:
        response = requests.post(
            settings.QWEN_OMNI_ENDPOINT,
            headers=headers,
            data=json.dumps(payload),
            timeout=60
        )
        response.raise_for_status()
    except Exception as e:
        raise QwenClientError(f"调用 Qwen2.5-Omni API 失败：{e}")

    result = response.json()
    # 6. 解析返回：假设 Qwen 返回格式与官方示例一致
    try:
        assistant_content = result["choices"][0]["message"]["content"]
        diagnosis = json.loads(assistant_content)
    except (KeyError, json.JSONDecodeError) as e:
        raise QwenClientError(f"解析 Qwen2.5-Omni 返回内容失败：{e}\n返回内容：{result}")

    return diagnosis
