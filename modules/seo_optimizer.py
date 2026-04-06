"""
SEO 최적화 검증 모듈 (지능형 버전)
긴 키워드에 대한 유연한 채점 및 핵심 단어 분석 기능을 포함합니다.
"""
import re
from bs4 import BeautifulSoup


def _get_core_keywords(keyword: str) -> list[str]:
    """긴 키워드에서 핵심 단어를 추출합니다 (예: '신청 조건' -> ['신청', '조건'])"""
    words = keyword.split()
    return [w for w in words if len(w) >= 2 and w not in ["및", "또는", "의", "를", "가", "이"]]


def _check_fuzzy_match(target_text: str, core_keywords: list[str], threshold: float = 0.6) -> bool:
    """핵심 단어들이 목표 텍스트에 충분히 포함되어 있는지 확인합니다 (유연한 매칭)"""
    if not core_keywords:
        return False
    matches = sum(1 for kw in core_keywords if kw.lower() in target_text.lower())
    return (matches / len(core_keywords)) >= threshold


def analyze_seo(content: dict, keyword: str) -> dict:
    """
    생성된 블로그 콘텐츠의 SEO 점수를 지능적으로 분석합니다.
    """
    title = content.get("title", "")
    html = content.get("content", "")

    # HTML → 텍스트
    soup = BeautifulSoup(html, "html5lib")
    text = soup.get_text(separator=" ", strip=True)

    # 롱테일 키워드 판단 (10자 이상)
    is_long_tail = len(keyword) >= 10
    core_kws = _get_core_keywords(keyword) if is_long_tail else [keyword]
    
    # 기준값 조정
    title_max = 75 if is_long_tail else 60
    meta_max = 170 if is_long_tail else 155
    min_density = 0.5 if is_long_tail else 1.0
    max_density = 5.0 if is_long_tail else 3.0

    checks = {}

    # 1. 제목 검사 (길이 + 포함 여부)
    checks["제목 길이 적절성"] = 30 <= len(title) <= title_max
    
    exact_title = keyword.lower() in title.lower()
    fuzzy_title = is_long_tail and _check_fuzzy_match(title, core_kws, 0.7)
    checks["제목에 키워드 포함"] = exact_title or fuzzy_title

    # 2. 메타 설명 검사
    meta = content.get("meta_description", "")
    checks["메타설명 길이 적절성"] = 100 <= len(meta) <= meta_max
    
    exact_meta = keyword.lower() in meta.lower()
    fuzzy_meta = is_long_tail and _check_fuzzy_match(meta, core_kws, 0.7)
    checks["메타설명에 키워드 포함"] = exact_meta or fuzzy_meta

    # 3. 본문 길이

    word_count = len(text)
    checks["본문 길이 (1000자 이상)"] = word_count >= 1000

    # 4. 키워드 밀도 (긴 키워드는 유연하게)
    keyword_count = text.lower().count(keyword.lower())
    if is_long_tail and keyword_count < 2:
        # 긴 키워드가 정확히 매칭되지 않는 경우 핵심어 빈도로 대체 계산 (보정)
        avg_core_count = sum(text.lower().count(cw.lower()) for cw in core_kws) / len(core_kws)
        density = (avg_core_count * len(keyword)) / max(len(text), 1) * 100
    else:
        density = (keyword_count * len(keyword)) / max(len(text), 1) * 100
    
    checks[f"키워드 밀도 ({min_density}~{max_density}%)"] = min_density <= density <= max_density

    # 5. 첫 문단 키워드
    first_p = soup.find("p")
    first_p_text = first_p.get_text().lower() if first_p else ""
    checks["첫 문단에 키워드 포함"] = (keyword.lower() in first_p_text) or (is_long_tail and _check_fuzzy_match(first_p_text, core_kws, 0.6))

    # 6. 소제목 구조
    h2_tags = soup.find_all("h2")
    h3_tags = soup.find_all("h3")
    checks["H2 소제목 (3개 이상)"] = len(h2_tags) >= 3
    checks["H3 소제목 존재"] = len(h3_tags) >= 1
    
    sub_text = " ".join([h.get_text().lower() for h in h2_tags + h3_tags])
    exact_sub = keyword.lower() in sub_text
    fuzzy_sub = is_long_tail and _check_fuzzy_match(sub_text, core_kws, 0.8)
    checks["소제목에 키워드 포함"] = exact_sub or fuzzy_sub

    # 7. 기타 (리스트, 태그)
    checks["리스트 활용 (가독성)"] = len(soup.find_all(["ul", "ol"])) >= 1
    tags = content.get("tags", [])
    checks["태그 등록 (3개 이상)"] = len(tags) >= 3


    # ── 점수 계산 ──
    passed = sum(1 for v in checks.values() if v)
    total = len(checks)
    score = int(passed / total * 100)

    # ── 개선 제안 생성 (지능형) ──
    suggestions = []
    if not checks.get("제목 길이 적절성"):
        suggestions.append(f"제목 길이를 {30}~{title_max}자로 조정하세요 (현재: {len(title)}자)")
    if not checks["제목에 키워드 포함"]:
        suggestions.append(f"제목에 '{keyword}'의 핵심 단어들을 더 배치하세요.")

    if not checks.get("본문 길이 (1000자 이상)"):
        suggestions.append(f"본문 내용이 부족합니다 (현재 {word_count}자). 사례나 팁을 추가해 보세요.")
    if density > max_density:
        suggestions.append(f"키워드가 너무 자주 등장합니다 (현재 {density:.1f}%). 자연스러운 대명사로 바꾸세요.")
    elif density < min_density:
        suggestions.append(f"핵심 키워드 언급이 적습니다. 문맥상 자연스럽게 1~2회 더 넣어주세요.")

    result = {
        "score": score,
        "checks": checks,
        "suggestions": suggestions,
        "stats": {
            "word_count": word_count,
            "keyword_density": round(density, 2),
            "h2_count": len(h2_tags),
            "h3_count": len(h3_tags),
            "list_count": len(soup.find_all(["ul", "ol"])),
            "is_long_tail": is_long_tail

        },
    }

    print(f"\n📊 지능형 SEO 분석: {score}/100 {'(롱테일 모드)' if is_long_tail else ''}")
    for check_name, passed in checks.items():
        icon = "✅" if passed else "❌"
        print(f"  {icon} {check_name}")

    if suggestions:
        print(f"\n💡 개선 제안:")
        for s in suggestions:
            print(f"  → {s}")

    return result
