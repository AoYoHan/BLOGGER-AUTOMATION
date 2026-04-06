"""
SEO 최적화 검증 모듈
생성된 콘텐츠의 SEO 점수를 분석하고 개선 제안을 제공합니다.
"""
import re
from bs4 import BeautifulSoup


def analyze_seo(content: dict, keyword: str) -> dict:
    """
    생성된 블로그 콘텐츠의 SEO 점수를 분석합니다.
    
    Args:
        content: {"title", "meta_description", "tags", "content"(HTML)}
        keyword: 타겟 키워드
    
    Returns:
        dict: {"score": int, "checks": dict, "suggestions": list}
    """
    title = content.get("title", "")
    html = content.get("content", "")

    # HTML → 텍스트
    soup = BeautifulSoup(html, "html5lib")
    text = soup.get_text(separator=" ", strip=True)

    # ── SEO 검사 항목 ──
    checks = {}

    # 1. 제목 검사
    checks["제목 길이 (30~60자)"] = 30 <= len(title) <= 60
    checks["제목에 키워드 포함"] = keyword.lower() in title.lower()

    # 3. 본문 검사
    word_count = len(text)
    checks["본문 길이 (1000자 이상)"] = word_count >= 1000

    # 4. 키워드 밀도
    keyword_count = text.lower().count(keyword.lower())
    density = (keyword_count * len(keyword)) / max(len(text), 1) * 100
    checks["키워드 밀도 (1~3%)"] = 1.0 <= density <= 3.0

    # 5. 첫 문단에 키워드
    first_p = soup.find("p")
    if first_p:
        checks["첫 문단에 키워드 포함"] = keyword.lower() in first_p.get_text().lower()
    else:
        checks["첫 문단에 키워드 포함"] = False

    # 6. 소제목 구조
    h2_tags = soup.find_all("h2")
    h3_tags = soup.find_all("h3")
    checks["H2 소제목 (3개 이상)"] = len(h2_tags) >= 3
    checks["H3 소제목 존재"] = len(h3_tags) >= 1
    checks["소제목에 키워드 포함"] = any(keyword.lower() in h.get_text().lower() for h in h2_tags + h3_tags)

    # 7. 리스트 구조
    lists = soup.find_all(["ul", "ol"])
    checks["리스트 활용 (가독성)"] = len(lists) >= 1

    # ── 점수 계산 ──
    passed = sum(1 for v in checks.values() if v)
    total = len(checks)
    score = int(passed / total * 100)

    # ── 개선 제안 생성 ──
    suggestions = []
    if not checks.get("제목 길이 (30~60자)"):
        suggestions.append(f"제목 길이를 30~60자로 조정하세요 (현재: {len(title)}자)")
    if not checks.get("제목에 키워드 포함"):
        suggestions.append(f"제목에 '{keyword}' 키워드를 포함하세요")
    if not checks.get("본문 길이 (1000자 이상)"):
        suggestions.append(f"본문을 1000자 이상으로 늘리세요 (현재: {word_count}자)")
    if not checks.get("키워드 밀도 (1~3%)"):
        suggestions.append(f"키워드 밀도를 1~3%로 조정하세요 (현재: {density:.1f}%)")
    if not checks.get("첫 문단에 키워드 포함"):
        suggestions.append(f"첫 문단에 '{keyword}' 키워드를 자연스럽게 포함하세요")
    if not checks.get("H2 소제목 (3개 이상)"):
        suggestions.append(f"H2 소제목을 최소 3개 이상 사용하세요 (현재: {len(h2_tags)}개)")
    if not checks.get("리스트 활용 (가독성)"):
        suggestions.append("불릿 포인트나 번호 리스트를 활용하여 가독성을 높이세요")

    result = {
        "score": score,
        "checks": checks,
        "suggestions": suggestions,
        "stats": {
            "word_count": word_count,
            "keyword_count": keyword_count,
            "keyword_density": round(density, 2),
            "h2_count": len(h2_tags),
            "h3_count": len(h3_tags),
            "list_count": len(lists),
        },
    }

    # 결과 출력
    print(f"\n📊 SEO 점수: {score}/100")
    for check_name, passed in checks.items():
        icon = "✅" if passed else "❌"
        print(f"  {icon} {check_name}")
    if suggestions:
        print(f"\n💡 개선 제안:")
        for s in suggestions:
            print(f"  → {s}")

    return result
