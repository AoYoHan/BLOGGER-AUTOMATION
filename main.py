"""
🚀 AI 블로그 자동 생성 파이프라인
Google Sheets에서 키워드를 읽어 → AI로 글 생성 → 이미지 생성 → 승인 후 Blogger 게시

사용법:
    python main.py generate     # 대기 키워드 → 초안 생성
    python main.py publish      # 승인된 초안 → Blogger 게시
    python main.py init         # 시트 초기화 (최초 1회)
    python main.py status       # 현재 상태 확인
"""
import argparse
import os
import sys
import time
from datetime import datetime, timedelta

from modules.sheets_manager import SheetsManager
from modules.keyword_research import research_keyword
from modules.content_generator import generate_blog_post
from modules.image_generator import generate_images_for_post
from modules.thumbnail_creator import create_thumbnail
from modules.drive_manager import DriveManager
from modules.seo_optimizer import analyze_seo
from modules.blogger_publisher import BloggerPublisher
from modules.indexing_manager import request_indexing
from config.settings import (
    STATUS_WAITING, STATUS_PAUSED, STATUS_RESEARCHING, STATUS_GENERATING, STATUS_REVIEW, 
    STATUS_PUBLISHED, STATUS_ERROR, MIN_SEO_SCORE, SHEET_DRAFTS, TARGET_YEAR,
    DELAY_BETWEEN_KEYWORDS
)


def cmd_init():
    """Google Sheets 초기화 (시트 구조 생성)"""
    print("=" * 60)
    print("📋 Google Sheets 초기화")
    print("=" * 60)
    sheets = SheetsManager()
    sheets.initialize_sheets()
    print("\n✅ 초기화 완료! Google Sheets에서 '키워드관리' 시트에 키워드를 입력하세요.")


def cmd_generate():
    """대기 중인 키워드 → AI 초안 생성"""
    print("=" * 60)
    print("🚀 AI 블로그 초안 생성 시작")
    print("=" * 60)

    sheets = SheetsManager()
    drive = DriveManager()

    # 대기 중인 키워드 가져오기
    pending = sheets.get_pending_keywords()
    if not pending:
        print("\n📭 대기 중인 키워드가 없습니다.")
        print("   Google Sheets '키워드관리' 시트에 키워드를 추가하세요.")
        return

    print(f"\n📝 처리할 키워드: {len(pending)}개")
    for kw in pending:
        print(f"  • {kw['keyword']} (톤: {kw['tone']})")

    for item in pending:
        keyword = item["keyword"]
        tone = item["tone"]
        color = item["color"]
        row = item["row"]
        related_kws = item.get("related_keywords", "")
        intent_kw = item.get("search_intent", "")

        # 키워드 간 지연 (무료 티어 쿼터 관리)
        if pending.index(item) > 0:
            print(f"\n⏳ 다음 키워드 처리 전 대기 중 ({DELAY_BETWEEN_KEYWORDS}초)... ☕")
            time.sleep(DELAY_BETWEEN_KEYWORDS)

        try:
            print(f"\n{'─' * 50}")
            print(f"🔄 처리 중: '{keyword}'")
            print(f"{'─' * 50}")

            # ── 1단계: 키워드 리서치 ──
            if related_kws:
                print(f"  ⏭️ 시트에 연관키워드가 지정되어 리서치 API 통신을 생략합니다.")
                sheets.update_keyword_status(row, STATUS_GENERATING)
                research = {
                    "keyword": keyword,
                    "suggestions": [],
                    "lsi_keywords": [],
                    "longtail_keywords": [],
                    "search_intent": intent_kw or "정보형",
                    "intent_detail": "",
                    "recommended_topics": [],
                    "target_audience": "일반 독자",
                    "content_angle": "",
                    "all_related": [k.strip() for k in related_kws.split(",") if k.strip()]
                }
            else:
                sheets.update_keyword_status(row, STATUS_RESEARCHING)
                research = research_keyword(keyword, target_year=TARGET_YEAR)

                # 연관 키워드를 시트에 업데이트
                related_text = ", ".join(research["all_related"][:10])
                sheets.update_keyword_status(
                    row, STATUS_GENERATING,
                    related=related_text,
                    intent=research["search_intent"]
                )

            # ── 2단계: AI 콘텐츠 생성 ──
            print(f"  ⏳ 단계 간 지연 중 (2초)...")
            time.sleep(2)
            content = generate_blog_post(keyword, research, tone, color, target_year=TARGET_YEAR)

            # ── 3단계: SEO 분석 ──
            seo = analyze_seo(content, keyword)
            sheets.update_keyword_status(row, STATUS_GENERATING, seo_score=str(seo["score"]))

            # SEO 점수가 낮으면 1회 재생성 시도
            if seo["score"] < MIN_SEO_SCORE:
                print(f"\n⚠️ SEO 점수 {seo['score']}점 → 최적화 재생성 중...")
                feedback = "SEO 개선 사항: " + "; ".join(seo["suggestions"][:3])
                from modules.content_generator import regenerate_with_feedback
                content = regenerate_with_feedback(keyword, content, feedback, color)
                seo = analyze_seo(content, keyword)
                sheets.update_keyword_status(row, STATUS_GENERATING, seo_score=str(seo["score"]))

            # ── 4단계: AI 이미지 프롬프트 생성 (이미지 생성 대신) ──
            images = generate_images_for_post(keyword, content)
            image_prompts = images.get("all_prompts_text", "")

            # ── 5단계: 썸네일 생성 건너뛰기 ──
            # (썸네일 열이 삭제되어 더 이상 필요 없음)

            # ── 6단계: Google Drive 업로드 ──
            drive_result = drive.upload_post_images(keyword, images, content["content"])

            # ── 7단계: 로컬 캐시 저장 및 초안검토 시트에 등록 ──
            # 본문 HTML 로컬 저장
            if not os.path.exists("drafts"):
                os.makedirs("drafts")
            
            safe_kw = "".join(x for x in keyword if x.isalnum() or x in " -_").strip()
            cache_path = f"drafts/{safe_kw}.html"
            with open(cache_path, "w", encoding="utf-8") as f:
                f.write(content["content"])
            print(f"  💾 본문 HTML 로컬 저장 완료: {cache_path}")


            # Drive에 생성된 Google Doc 링크 사용
            doc_url = drive_result.get("doc_url") or drive_result["folder_url"]

            # 기본 예약시간 (+1시간)
            default_publish_time = (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M")

            sheets.add_draft(
                keyword=keyword,
                title=content["title"],
                meta=content["meta_description"],

                doc_url=doc_url,
                image_prompts=image_prompts,
                publish_time=default_publish_time,
                approval="승인"
            )

            # 상태 업데이트
            sheets.update_keyword_status(row, STATUS_REVIEW, seo_score=str(seo["score"]))

            print(f"\n✅ '{keyword}' 초안 생성 완료!")
            print(f"  📊 SEO: {seo['score']}점 | 제목: {content['title'][:40]}...")
            print(f"  🖼️ 이미지: Drive에 업로드 완료")

        except Exception as e:
            print(f"\n❌ '{keyword}' 처리 오류: {e}")
            sheets.update_keyword_status(row, STATUS_ERROR)
            import traceback
            traceback.print_exc()
            continue

    print(f"\n{'=' * 60}")
    print("🎉 초안 생성 완료!")
    print("📋 Google Sheets '초안검토' 시트에서 결과를 확인하세요.")
    print("✅ 게시할 글의 '승인' 열에 '승인'이라고 입력한 후 'python main.py publish'를 실행하세요.")
    print(f"{'=' * 60}")


def cmd_publish():
    """승인된 초안 → Blogger 게시"""
    print("=" * 60)
    print("📤 승인된 글 Blogger 게시")
    print("=" * 60)

    sheets = SheetsManager()
    blogger = BloggerPublisher()

    # 블로그 정보 확인
    blog_info = blogger.get_blog_info()
    if blog_info:
        print(f"  📝 블로그: {blog_info['name']} ({blog_info['url']})")

    # 승인된 초안 가져오기
    approved = sheets.get_approved_drafts()
    if not approved:
        print("\n📭 승인된 초안이 없습니다.")
        print("   '초안검토' 시트에서 게시할 글의 '승인' 열에 '승인'이라고 입력하세요.")
        return

    print(f"\n📝 게시할 글: {len(approved)}개")
    for draft in approved:
        print(f"  • {draft['title'][:50]}...")

    for draft in approved:
        try:
            # 글 본문은 content_generator에서 생성한 데이터를 재사용
            # (현재는 간단 버전: 제목+메타설명으로 게시)
            # 실제로는 캐시된 전체 HTML을 사용해야 함
            
            # 키워드로 기존 생성 데이터 조회 (여기서는 재생성)
            keyword = draft["keyword"]
            print(f"\n🔄 게시 준비: '{keyword}'")
            
            # 1. 로컬 캐시에서 본문 HTML 로드 시도
            content_html = ""
            safe_kw = "".join(x for x in keyword if x.isalnum() or x in " -_").strip()
            cache_path = f"drafts/{safe_kw}.html"
            
            if os.path.exists(cache_path):
                with open(cache_path, "r", encoding="utf-8") as f:
                    content_html = f.read()
                print(f"  📂 로컬 캐시 사용: {cache_path}")
            
            if not content_html:
                # 시트에 혹시 남아있을 수 있는 데이터 확인
                content_html = draft.get("본문HTML", "")
            
            if not content_html:
                print(f"  ⚠️ '{keyword}'의 본문 HTML을 찾을 수 없습니다. {TARGET_YEAR}년 기준으로 재생성을 시도합니다.")
                research = research_keyword(keyword, target_year=TARGET_YEAR)
                content = generate_blog_post(keyword, research, target_year=TARGET_YEAR)
                content_html = content["content"]
            
            # 예약 시간 처리
            publish_date = None
            raw_date = draft.get("예약시간", "").strip()
            if raw_date:
                try:
                    # 다양한 형식 지원 (YYYY-MM-DD HH:MM:SS 또는 YYYY-MM-DD HH:MM)
                    content_date = None
                    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M"]:
                        try:
                            content_date = datetime.strptime(raw_date, fmt)
                            break
                        except: continue
                    
                    if content_date:
                        # RFC3339 형식으로 변환 (KST +09:00 가정)
                        publish_date = content_date.strftime("%Y-%m-%dT%H:%M:%S+09:00")
                except Exception as e:
                    print(f"  ⚠️ 예약시간 형식 오류 ('{raw_date}'): {e}. 즉시 발행으로 진행합니다.")

            # Blogger에 게시
            result = blogger.publish_post(
                title=draft["title"],
                content_html=content_html,
                labels=[], # 태그는 사용하지 않기로 함
                meta_description=draft.get("meta_description", ""), # 시트의 메타설명 전달
                is_draft=False,
                publish_date=publish_date
            )

            # 🌐 Google Search Console 색인 자동 요청 추가
            post_url = result.get("url")
            indexing_status = "건너뜀"
            if post_url:
                indexing_status = request_indexing(post_url)

            # 시트 업데이트
            sheets.mark_draft_published(draft["row"])
            today = datetime.now().strftime("%Y-%m-%d")

            # 키워드관리 시트 상태 업데이트
            ws = sheets.spreadsheet.worksheet("키워드관리")
            records = ws.get_all_records()
            for i, rec in enumerate(records, start=2):
                if str(rec.get("키워드", "")).strip() == keyword:
                    sheets.update_keyword_status(i, STATUS_PUBLISHED)
                    break

            # 게시현황 시트에 기록
            sheets.add_published_record(
                keyword=keyword,
                title=draft["title"],
                post_url=result["url"],
                image_folder_url=draft.get("doc_url", ""),
                published_date=today,
                indexing_status=indexing_status
            )

            print(f"  ✅ 게시 완료: {result['url']}")
            
            # 다음 글 게시 전 지연 (Rate Limit 방지)
            print(f"  ⏳ 다음 게시 대기 중 (5초)...")
            time.sleep(5)

        except Exception as e:
            print(f"  ❌ '{draft['keyword']}' 게시 오류: {e}")
            import traceback
            traceback.print_exc()
            continue

    print(f"\n{'=' * 60}")
    print("🎉 게시 완료!")
    print("📋 Google Sheets '게시현황' 시트에서 결과를 확인하세요.")
    print(f"{'=' * 60}")


def cmd_status():
    """현재 상태 확인"""
    print("=" * 60)
    print("📊 현재 상태")
    print("=" * 60)

    sheets = SheetsManager()

    # 키워드관리 현황
    ws = sheets.spreadsheet.worksheet("키워드관리")
    records = ws.get_all_records()
    keywords = [r for r in records if str(r.get("키워드", "")).strip()]

    print(f"\n📋 키워드관리: 총 {len(keywords)}개")
    status_count = {}
    for r in keywords:
        s = str(r.get("상태", "⏳대기")).strip() or "⏳대기"
        status_count[s] = status_count.get(s, 0) + 1
    
    for s, count in status_count.items():
        print(f"  {s}: {count}개")

    # 초안검토 현황
    try:
        ws2 = sheets.spreadsheet.worksheet(SHEET_DRAFTS)
        drafts = ws2.get_all_records()
        pending_review = sum(1 for d in drafts if str(d.get("승인", "")).strip() == "대기")
        approved = sum(1 for d in drafts if str(d.get("승인", "")).strip() in ["승인", "✅"])
        published = sum(1 for d in drafts if "게시" in str(d.get("승인", "")))
        print(f"\n📝 초안검토: 검토대기 {pending_review}개 | 승인 {approved}개 | 게시됨 {published}개")
    except Exception:
        pass

    # 게시현황
    try:
        ws3 = sheets.spreadsheet.worksheet("게시현황")
        published_all = ws3.get_all_records()
        total_published = len([p for p in published_all if str(p.get("키워드", "")).strip()])
        print(f"\n✅ 게시현황: 총 {total_published}개 게시됨")
    except Exception:
        pass


def cmd_auto():
    """Generate + Publish (1회 실행)"""
    print("=" * 60)
    print("🤖 통합 자동화 프로세스 시작 (1회)")
    print("=" * 60)
    cmd_generate()
    print("\n" + "-" * 40)
    print("✍️ 생성 작업 완료! 바로 발행 작업을 시작합니다...")
    cmd_publish()
    print("=" * 60)
    print("✅ 통합 프로세스 완료!")


def cmd_loop():
    """Generate + Publish 무한 루프 (1시간 간격)"""
    print("=" * 60)
    print("🔄 블로그 자동화 무한 루프 시작 (종료: Ctrl+C)")
    print("=" * 60)
    
    interval = 3600 # 1시간
    
    try:
        while True:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n🚀 [{now}] 새로운 주기 시작...")
            
            cmd_generate()
            print("\n" + "-" * 20)
            cmd_publish()
            
            next_run = (datetime.now() + timedelta(seconds=interval)).strftime("%H:%M:%S")
            print(f"\n😴 다음 실행까지 대기 중... (다음 예정: {next_run})")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\n👋 자동화 루프를 종료합니다.")


def main():
    parser = argparse.ArgumentParser(
        description="🚀 AI 블로그 자동 생성 시스템",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예:
  python main.py init       # 1. 시트 초기화 (최초 1회)
  python main.py generate   # 2. 대기 키워드 → AI 초안 생성
  python main.py publish    # 3. 승인된 초안 → Blogger 게시
  python main.py status     # 4. 현재 상태 확인
  python main.py auto       # 5. 생성 + 게시 (1회 통합)
  python main.py loop       # 6. 생성 + 게시 (1시간 간격 루프)
        """
    )
    parser.add_argument(
        "command",
        choices=["init", "generate", "publish", "status", "auto", "loop"],
        help="실행할 명령"
    )

    args = parser.parse_args()

    commands = {
        "init": cmd_init,
        "generate": cmd_generate,
        "publish": cmd_publish,
        "status": cmd_status,
        "auto": cmd_auto,
        "loop": cmd_loop,
    }

    commands[args.command]()


if __name__ == "__main__":
    main()
