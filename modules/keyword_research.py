"""
키워드 리서치 모듈
Google Autocomplete + Gemini API로 키워드 분석을 수행합니다.
"""
import json
import os
import sys
import requests
from urllib.parse import quote

import google.generativeai as genai
from google.api_core import exceptions
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config.settings import GEMINI_API_KEY, DELAY_BEFORE_API_CALL, get_current_api_key, switch_api_key, get_total_api_keys


# Gemini 초기화
genai.configure(api_key=get_current_api_key())


def get_google_suggestions(keyword: str) -> list[str]:
    """
    Google 자동완성 API를 사용하여 연관 검색어를 수집합니다. (무료)
    """
    try:
        encoded = quote(keyword)
        url = f"http://suggestqueries.google.com/complete/search?client=firefox&q={encoded}&hl=ko"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        suggestions = data[1] if len(data) > 1 else []
        # 원래 키워드 제외
        return [s for s in suggestions if s.lower() != keyword.lower()]
    except Exception as e:
        print(f"  ⚠️ Google Suggestions 오류: {e}")
        return []


def analyze_with_gemini(keyword: str, suggestions: list[str], target_year: str = "2026") -> dict:
    """
    Gemini API로 키워드를 심층 분석합니다.
    - LSI 키워드
    - 롱테일 키워드
    - 검색 의도 분석
    - 추천 글 방향
    """
    suggestion_text = ", ".join(suggestions[:10]) if suggestions else "없음"

    prompt = f"""당신은 SEO 키워드 분석 전문가입니다.

아래 키워드에 대해 {target_year}년 최신 트렌드와 정보를 바탕으로 JSON 형식으로 분석 결과를 제공해주세요.
특히 {target_year}년에 새롭게 시행되는 정책, 규정, 트렌드를 반드시 반영해야 합니다.

[메인 키워드]: {keyword}
[참고 연관 검색어]: {suggestion_text}

다음 JSON 형식으로만 응답하세요 (다른 텍스트 없이):
{{
    "lsi_keywords": ["LSI 키워드 10개"],
    "longtail_keywords": ["롱테일 키워드 5개"],
    "search_intent": "정보형/거래형/네비게이션형 중 하나",
    "intent_detail": "검색 의도 상세 설명 (1문장, 연도는 문맥에 따라 사용)",
    "recommended_topics": ["최신 정보를 반영한 추천 글 방향/소제목 5개 (소제목 마다 연도를 넣지 말고 필요한 경우만 언급)"],
    "target_audience": "목표 독자층 설명",
    "content_angle": "전문성이 느껴지는 최신 정보 중심의 글 작성 각도 추천"
}}"""

    try:
        model = genai.GenerativeModel("gemini-3-flash-preview")
        
        # 재시도 로직 적용 (현재 키 개수에 비례)
        max_retries = get_total_api_keys() * 2
        response = None
        for i in range(max_retries):
            try:
                # 연속 호출 방지를 위한 미세 지연
                if DELAY_BEFORE_API_CALL > 0:
                    time.sleep(DELAY_BEFORE_API_CALL)
                response = model.generate_content(prompt)
                break
            except exceptions.ResourceExhausted:
                if i < max_retries - 1:
                    switch_api_key()
                    genai.configure(api_key=get_current_api_key())
                    model = genai.GenerativeModel("gemini-3-flash-preview")
                    
                    # 모든 키를 한 번씩 순회한 경우에만 대기
                    if (i + 1) % get_total_api_keys() == 0:
                        wait_time = 30
                        print(f"  ⚠️ 모든 키 한도 초과. {wait_time}초 후 재시도... ({i+1}/{max_retries})")
                        time.sleep(wait_time)
                else: raise
        
        text = response.text.strip()

        # JSON 블록 추출
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        return json.loads(text)

    except json.JSONDecodeError:
        print(f"  ⚠️ Gemini 응답 파싱 실패, 기본값 사용")
        return {
            "lsi_keywords": suggestions[:5],
            "longtail_keywords": [],
            "search_intent": "정보형",
            "intent_detail": "분석 실패",
            "recommended_topics": [],
            "target_audience": "일반 독자",
            "content_angle": "기본 정보 제공",
        }
    except Exception as e:
        print(f"  ❌ Gemini 키워드 분석 오류: {e}")
        return {
            "lsi_keywords": suggestions[:5],
            "longtail_keywords": [],
            "search_intent": "정보형",
            "intent_detail": str(e),
            "recommended_topics": [],
            "target_audience": "일반 독자",
            "content_angle": "기본 정보 제공",
        }


def research_keyword(keyword: str, target_year: str = "2026") -> dict:
    """
    키워드 리서치 전체 파이프라인을 실행합니다.
    
    Returns:
        dict: {
            "keyword": str,
            "suggestions": list,      # Google 자동완성 결과
            "lsi_keywords": list,      # LSI 키워드
            "longtail_keywords": list,  # 롱테일 키워드
            "search_intent": str,       # 검색 의도
            "recommended_topics": list, # 추천 소제목
            "all_related": list,        # 전체 연관 키워드 통합
        }
    """
    print(f"\n🔍 키워드 리서치: '{keyword}'")

    # 1단계: Google 자동완성
    print("  📡 Google Autocomplete 수집 중...")
    suggestions = get_google_suggestions(keyword)
    print(f"  → {len(suggestions)}개 연관 검색어 수집")

    # 2단계: Gemini 분석
    print(f"  🤖 Gemini {target_year}년 데이터 분석 중...")
    analysis = analyze_with_gemini(keyword, suggestions, target_year)
    print(f"  → 검색 의도: {analysis.get('search_intent', 'N/A')}")
    print(f"  → LSI 키워드 {len(analysis.get('lsi_keywords', []))}개")

    # 통합
    all_related = list(set(
        suggestions +
        analysis.get("lsi_keywords", []) +
        analysis.get("longtail_keywords", [])
    ))

    return {
        "keyword": keyword,
        "suggestions": suggestions,
        "lsi_keywords": analysis.get("lsi_keywords", []),
        "longtail_keywords": analysis.get("longtail_keywords", []),
        "search_intent": analysis.get("search_intent", "정보형"),
        "intent_detail": analysis.get("intent_detail", ""),
        "recommended_topics": analysis.get("recommended_topics", []),
        "target_audience": analysis.get("target_audience", ""),
        "content_angle": analysis.get("content_angle", ""),
        "all_related": all_related,
    }
