"""
Google Indexing API 관리 모듈
블로그 포스트 게시 후 즉시 Google에 색인 생성을 요청합니다.
"""
import os
import sys
from googleapiclient.discovery import build

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from modules.google_auth import get_google_credentials


def request_indexing(url: str):
    """
    Google Indexing API를 통해 URL의 색인(발견 및 수집)을 요청합니다.
    
    Args:
        url: 색인을 요청할 블로그 포스트 URL
    """
    try:
        creds = get_google_credentials()
        
        # Indexing API 서비스 빌드
        service = build("indexing", "v3", credentials=creds)
        
        body = {
            "url": url,
            "type": "URL_UPDATED" # 새 URL 생성 또는 기존 URL 업데이트
        }
        
        print(f"\n  📡 Google Search Console 색인 자동 요청 중...")
        print(f"     대상: {url}")
        
        result = service.urlNotifications().publish(body=body).execute()
        
        # 결과 확인
        metadata = result.get("urlNotificationMetadata", {})
        latest_update = metadata.get("latestUpdate", {})
        notification_type = latest_update.get("type", "Unknown")
        
        print(f"  ✅ 색인 요청 완료! (상태: {notification_type})")
        return f"성공 ({notification_type})"
        
    except Exception as e:
        print(f"  ⚠️ Google Indexing API 요청 실패: {e}")
        return "실패"

if __name__ == "__main__":
    # 테스트용 (실제 실행 시 주의)
    # test_url = "https://your-blog-url.blogspot.com/test-post.html"
    # request_indexing(test_url)
    pass
