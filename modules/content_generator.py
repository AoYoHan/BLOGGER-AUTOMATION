"""
AI 콘텐츠 생성 모듈
Gemini API (유료)를 사용하여 SEO 최적화된 블로그 글을 생성합니다.
"""
import json
import os
import sys
import re

import google.generativeai as genai
from google.api_core import exceptions
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config.settings import GEMINI_API_KEY, MIN_WORD_COUNT, DELAY_BEFORE_API_CALL, get_current_api_key, switch_api_key, get_total_api_keys


# Gemini 초기화
genai.configure(api_key=get_current_api_key())


def _apply_subheading_styles(content: str, color: str = "#3d94f6") -> str:
    """
    본문 HTML의 h2, h3 태그에 사용자 정의 스타일을 적용합니다.
    """
    if not content:
        return content

    # h2 스타일 (숫자로 시작하는 경우)
    h2_style = f"padding: 0.4em 1em 0.4em 0.5em; background: #e9efed; margin: 0.5em 0em; color: #000000; border-left: {color} 10px solid; font-weight: bold;"
    # h3 스타일
    h3_style = f"padding: 0.4em 1em 0.4em 0.5em; margin: 0.5em 0em; color: #000000; border-left: 5px solid {color}; border-bottom: 2px {color} solid; font-weight: bold;"

    def style_h2(match):
        tag_content = match.group(1)
        # 숫자로 시작하는지 확인 (예: 1., 2. 등)
        text_content = re.sub(r'<[^>]+>', '', tag_content)
        if re.match(r'^\s*\d+[\s.]', text_content) or text_content.strip().startswith('결론'):
            return f'<h2 class="is_numeric" style="{h2_style}">{tag_content}</h2>'
        return f'<h2>{tag_content}</h2>'

    # h2 처리
    content = re.sub(r'<h2[^>]*>(.*?)</h2>', style_h2, content, flags=re.DOTALL)
    # h3 처리
    content = re.sub(r'<h3[^>]*>(.*?)</h3>', f'<h3 style="{h3_style}">\\1</h3>', content, flags=re.DOTALL)
    
    return content


def generate_blog_post(keyword: str, research: dict, tone: str = "전문적이면서 친근한", color: str = "#3d94f6", target_year: str = "2026") -> dict:
    """
    Gemini API로 SEO 최적화된 블로그 글을 생성합니다.
    
    Args:
        keyword: 메인 키워드
        research: keyword_research.research_keyword()의 결과
        tone: 글의 톤앤매너
        color: 스타일 색상
        target_year: 기준 연도
    
    Returns:
        dict: {"title", "content" (HTML), "subtopics"}
    """
    related = ", ".join(research.get("all_related", [])[:15])
    topics = "\n".join(f"- {t}" for t in research.get("recommended_topics", []))
    intent = research.get("search_intent", "정보형")
    audience = research.get("target_audience", "일반 독자")
    angle = research.get("content_angle", "")

    prompt = f"""당신은 대한민국 최고의 SEO 전문 블로그 작가입니다. 반드시 {target_year}년 최신 정보와 데이터를 바탕으로 아래 조건에 맞춰 고품질 블로그 글을 작성하세요.

═══ 핵심 정보 ═══
[메인 키워드]: {keyword} (정보 출처 및 기준: {target_year}년 최신 데이터)
[연관 키워드]: {related}
[검색 의도]: {intent}
[목표 독자]: {audience}
[차별화 포인트]: {angle}
[톤앤매너]: {tone}

═══ 참고할 소제목 방향 ═══
{topics}

═══ 핵심 작성 규칙 (중요) ═══
1. 본문 분량: **SEO 점수 고득점을 위해 반드시 공백 제외 순수 텍스트 기준 {MIN_WORD_COUNT}자 이상(최대한 상세하게) 작성**하세요.
2. 연도 사용 주의: '{target_year}년'이라는 표현은 도입부나 핵심 수치, 정책 설명 등 "최신 정보임을 나타내야 하는 꼭 필요한 경우"에만 사용하세요. 글 전체에서 기계적인 반복은 절대 지양하고, 전체적으로 자연스럽게 읽혀야 합니다.
3. 제목: 클릭을 유도하는 매력적인 제목 (50~60자, 메인 키워드 포함, 제목에는 연도 제외)
4. 메타 설명: {target_year}년 최신 트렌드를 반영한 정보임을 강조 (120~155자, 메인 키워드 포함)
5. 구조 및 가독성:
   - 도입부: 현재 왜 이 정보가 중요한지 강조하는 훅(Hook). (연도는 여기서 언급 가능)
   - 본문: H2, H3 소제목으로 논리적 구조화 (**H2 소제목은 반드시 '1. ', '2. ', '3. '과 같이 숫자로 시작**해야 하며, 최소 4개의 H2를 포함하세요.)
   - 가독성 강화: **내용을 나열하거나 비교할 때는 반드시 표(Table) 또는 리스트(ul, ol)를 활용**하여 시각적으로 깔끔하게 구성하세요. 장황한 서술형 문장만 나열하는 것을 피하십시오.
   - 각 섹션마다 전문적인 예시나 팁을 포함하여 내용을 풍부하게 만드세요.
   - 문단은 3~4줄 이내로 짧게 작성하고, 반드시 `<p>` 태그로 감싸며 줄바꿈(\n)을 활용하세요.
6. SEO 최적화: 메인 키워드를 첫 문단과 소제목 중 1회 이상 자연스럽게 포함하세요. (소제목에 연도를 남발하지 마세요)
7. 이미지 위치 표시: 본문 중간에 <!-- IMAGE: 이미지 설명 --> 주석 삽입 (3~4개)

═══ 출력 형식 (JSON) ═══
다음 JSON 형식으로만 응답하세요:
{{
    "title": "매력적인 블로그 제목",
    "subtopics": ["1. 풍성한 첫번째 소제목", "2. 전문적인 두번째 소제목", "3. 유익한 세번째 소제목"],
    "content": "<h2>1. 첫번째 소제목</h2><p>본문 내용...</p>"
}}
"""
    print(f"\n✍️ 블로그 글 생성: '{keyword}'")
    print(f"  🤖 Gemini로 콘텐츠 생성 중... (약 30초)")

    def _generate_with_retry(model_name, prompt, config, max_retries_multiplier=2):
        max_retries = get_total_api_keys() * max_retries_multiplier
        # Initialize model with current API key
        genai.configure(api_key=get_current_api_key())
        model = genai.GenerativeModel(model_name)
        
        for i in range(max_retries):
            try:
                # 연속 호출 방지를 위한 미세 지연
                if DELAY_BEFORE_API_CALL > 0:
                    time.sleep(DELAY_BEFORE_API_CALL)
                return model.generate_content(prompt, generation_config=config)
            except exceptions.ResourceExhausted as e:
                if i < max_retries - 1:
                    switch_api_key()
                    genai.configure(api_key=get_current_api_key())
                    model = genai.GenerativeModel(model_name)
                    
                    if (i + 1) % get_total_api_keys() == 0:
                        wait_time = min(60, (i // get_total_api_keys() + 1) * 30)
                        print(f"  ⚠️ 모든 키 호출 한도 초과 (429). {wait_time}초 후 재시도 중... ({i+1}/{max_retries})")
                        time.sleep(wait_time)
                else:
                    print(f"  ❌ 최대 재시도 횟수를 초과했습니다.")
                    raise e
            except Exception as e:
                raise e

    try:
        response = _generate_with_retry(
            "gemini-3-flash-preview", 
            prompt,
            genai.types.GenerationConfig(
                temperature=0.8,
                max_output_tokens=8192,
            )
        )
        text = response.text.strip()

        # JSON 블록 추출
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        result = json.loads(text)
        
        # 기본값 보장
        result.setdefault("title", f"{keyword} - 완벽 가이드")
        result.setdefault("subtopics", [])
        result.setdefault("content", "<p>콘텐츠 생성 실패</p>")

        # 소제목 스타일링 및 상단 이미지 위치 추가
        if "content" in result:
            result["content"] = f"<p>&nbsp;이미지넣을 곳</p>\n" + result["content"]
            result["content"] = _apply_subheading_styles(result["content"], color)

        # 본문 길이 확인
        text_only = re.sub(r'<[^>]+>', '', result["content"])
        word_count = len(text_only)
        print(f"  ✅ 생성 완료! (제목: {result['title'][:40]}...)")
        print(f"  📝 본문 길이: {word_count}자")

        return result

    except json.JSONDecodeError as e:
        print(f"  ⚠️ JSON 파싱 실패: {e}")
        print(f"  📝 원본 응답으로 대체 처리...")
        # JSON 파싱 실패 시, 원본 텍스트를 content로 사용
        return {
            "title": f"{keyword} 가이드",
            "subtopics": [],
            "content": f"<p>{response.text}</p>" if response.text else "<p>생성 실패</p>",
        }
    except Exception as e:
        print(f"  ❌ 콘텐츠 생성 오류: {e}")
        raise


def regenerate_with_feedback(keyword: str, original_content: dict, feedback: str, color: str = "#3d94f6") -> dict:
    """
    사용자 피드백을 반영하여 글을 재생성합니다.
    """
    prompt = f"""이전에 생성한 블로그 글을 피드백에 따라 수정해주세요.

[키워드]: {keyword}
[이전 제목]: {original_content['title']}
[이전 본문 일부]: {original_content['content'][:1000]}...

[수정 요청사항]:
{feedback}

수정된 결과를 아래 JSON 형식으로 응답해주세요 (본문 분량: {MIN_WORD_COUNT}자 이상, **H2 소제목은 반드시 숫자로 시작**):
{{
    "title": "수정된 제목",
    "subtopics": ["1. 수정된 소제목1", "2. 수정된 소제목2"],
    "content": "<h2>1. ...</h2><p>...</p>"
}}
"""

    try:
        model = genai.GenerativeModel("gemini-3-flash-preview")
        
        # 재시도 로직 적용
        max_retries = get_total_api_keys() * 2
        for i in range(max_retries):
            try:
                response = model.generate_content(prompt)
                break
            except exceptions.ResourceExhausted:
                if i < max_retries - 1:
                    switch_api_key()
                    genai.configure(api_key=get_current_api_key())
                    model = genai.GenerativeModel("gemini-3-flash-preview")
                    
                    if (i + 1) % get_total_api_keys() == 0:
                        wait_time = 30
                        print(f"  ⚠️ 모든 키 한도 초과. {wait_time}초 후 재시도... ({i+1}/{max_retries})")
                        time.sleep(wait_time)
                else: raise
        
        text = response.text.strip()

        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        result = json.loads(text)
        if "content" in result:
            result["content"] = f"<p>&nbsp;이미지넣을 곳</p>\n" + result["content"]
            result["content"] = _apply_subheading_styles(result["content"], color)
        return result
    except Exception as e:
        print(f"  ❌ 재생성 오류: {e}")
        return original_content
