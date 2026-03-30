import os
import re
import time
import sys
from typing import Optional, List, Dict
from google import genai
from google.genai import types

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config.settings import GEMINI_API_KEY, get_current_api_key


# Imagen 3 클라이언트 초기화
client = genai.Client(api_key=get_current_api_key())


def generate_image_prompt(prompt: str, aspect_ratio: str = "16:9") -> str:
    """
    이미지 생성을 위한 텍스트 프롬프트를 반환합니다. (API 호출 안 함)
    """
    return f"[종횡비 {aspect_ratio}] {prompt}"


def generate_hero_image_prompt(keyword: str) -> str:
    """블로그 대표 이미지 프롬프트 생성"""
    prompt = (
        f"Professional and modern blog header image about '{keyword}', "
        f"clean and minimal design, vibrant colors, high quality, "
        f"no text, no watermark, live action"
    )
    return generate_image_prompt(prompt, aspect_ratio="16:9")


def generate_body_image_prompts(keyword: str, subtopics: List[str], max_images: int = 3) -> List[Dict]:
    """본문 삽입용 이미지 프롬프트 생성"""
    prompts = []
    topics_to_process = subtopics[:max_images]

    for i, topic in enumerate(topics_to_process, 1):
        prompt_text = (
            f"Minimalist illustration about '{topic}' in context of '{keyword}', "
            f"flat design style, modern, clean, blog article illustration, "
            f"no text, no watermark"
        )
        full_prompt = generate_image_prompt(prompt_text, aspect_ratio="4:3")
        prompts.append({"topic": topic, "prompt": full_prompt})
        
    return prompts


def extract_image_placeholders(html_content: str) -> list[str]:
    """
    HTML 콘텐츠에서 <!-- IMAGE: 설명 --> 주석을 추출합니다.
    """
    pattern = r'<!--\s*IMAGE:\s*(.+?)\s*-->'
    return re.findall(pattern, html_content)


def generate_images_for_post(keyword: str, content: dict) -> dict:
    """
    블로그 포스트에 필요한 이미지 프롬프트를 생성합니다.
    """
    print(f"\n📝 이미지 프롬프트 생성 시작: '{keyword}'")

    # 1. 대표 이미지 프롬프트
    hero_prompt = generate_hero_image_prompt(keyword)

    # 2. 본문 이미지 프롬프트
    placeholders = extract_image_placeholders(content.get("content", ""))
    topics_for_images = placeholders if placeholders else content.get("subtopics", [])
    body_prompts = generate_body_image_prompts(keyword, topics_for_images)

    # 3. 전체 프롬프트 텍스트 정리 (시트용)
    all_prompts_text = f"제목용: {hero_prompt}\n\n"
    for i, p in enumerate(body_prompts, 1):
        all_prompts_text += f"본문 {i}: {p['prompt']}\n"

    print(f"  🎉 총 {1 + len(body_prompts)}개 프롬프트 생성 완료!")

    return {
        "hero_prompt": hero_prompt,
        "body_prompts": body_prompts,
        "all_prompts_text": all_prompts_text,
        "hero": None, # 기존 코드 호환성 유지
        "body_images": []
    }
