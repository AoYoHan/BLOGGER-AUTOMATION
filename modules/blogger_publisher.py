"""
Blogger API 게시 모듈
Google Blogger API v3를 통해 블로그 포스트를 생성합니다.
"""
import os
import re
import sys

import time
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config.settings import BLOG_ID
from modules.google_auth import get_google_credentials


class BloggerPublisher:
    """Google Blogger API v3 게시 관리자"""

    def __init__(self):
        creds = get_google_credentials()
        self.service = build("blogger", "v3", credentials=creds)
        self.blog_id = BLOG_ID
        print(f"📝 Blogger API 연결됨 (Blog ID: {self.blog_id})")

    def _embed_images_in_html(self, html: str, drive_images: dict) -> str:
        """
        HTML 콘텐츠의 이미지 플레이스홀더를 Drive 이미지 URL로 교체합니다.
        """
        # 대표 이미지를 최상단에 삽입
        hero_url = drive_images.get("hero_url")
        if hero_url:
            hero_html = (
                f'<div style="text-align:center; margin-bottom:20px;">'
                f'<img src="{hero_url}" alt="대표 이미지" '
                f'style="max-width:100%; height:auto; border-radius:8px;" />'
                f'</div>\n'
            )
            html = hero_html + html

        # <!-- IMAGE: 설명 --> 플레이스홀더를 실제 이미지로 교체
        body_urls = drive_images.get("body_urls", [])
        placeholder_pattern = r'<!--\s*IMAGE:\s*(.+?)\s*-->'
        placeholders = re.findall(placeholder_pattern, html)

        for i, placeholder_desc in enumerate(placeholders):
            if i < len(body_urls):
                img_info = body_urls[i]
                img_html = (
                    f'<div style="text-align:center; margin:20px 0;">'
                    f'<img src="{img_info["url"]}" alt="{img_info["topic"]}" '
                    f'style="max-width:100%; height:auto; border-radius:8px;" />'
                    f'<p style="font-size:0.85em; color:#666; margin-top:8px;">'
                    f'{img_info["topic"]}</p>'
                    f'</div>'
                )
                html = html.replace(f"<!-- IMAGE: {placeholder_desc} -->", img_html, 1)

        return html

    def publish_post(self, title: str, content_html: str, labels: list[str],
                     meta_description: str = "", drive_images: dict = None,
                     is_draft: bool = False, publish_date: str = None) -> dict:
        """
        Blogger에 포스트를 게시합니다.
        
        Args:
            title: 포스트 제목
            content_html: HTML 본문
            labels: 태그/라벨 리스트
            meta_description: 검색 설명 (search description)
            drive_images: drive_manager.upload_post_images()의 결과
            is_draft: True면 초안으로 저장
            publish_date: 예약 발행 시간 (RFC3339 string, eg: 2024-03-21T10:00:00+09:00)
        
        Returns:
            dict: {"id", "url", "published", "status"}
        """
        # 이미지 삽입
        if drive_images:
            content_html = self._embed_images_in_html(content_html, drive_images)

        body = {
            "kind": "blogger#post",
            "blog": {"id": self.blog_id},
            "title": title,
            "content": content_html,
            "labels": labels,
        }

        # 예약 날짜 설정
        if publish_date:
            body["published"] = publish_date

        # 참고: Blogger API v3는 '검색 설명(Meta Description)' 설정을 공식적으로 지원하지 않습니다.
        # (API를 통해 시도해도 대시보드의 '검색 설명' 칸은 채워지지 않습니다.)
        # 향후 API가 업데이트될 가능성을 대비해 주석 처리해 둡니다.
        # if meta_description:
        #     body["customMetaData"] = meta_description

        print(f"\n📤 Blogger 게시 중: '{title[:50]}...'")
        if publish_date:
            print(f"  📅 예약 발행 모드: {publish_date}")
        else:
            print(f"  {'📋 초안 모드' if is_draft else '🌐 즉시 게시'}")

        max_retries = 3
        retry_delay = 5  # 초기 대기 시간 (초)

        for attempt in range(max_retries):
            try:
                post = self.service.posts().insert(
                    blogId=self.blog_id, body=body, isDraft=is_draft
                ).execute()

                result = {
                    "id": post.get("id"),
                    "url": post.get("url"),
                    "published": post.get("published"),
                    "status": post.get("status", "LIVE" if not is_draft else "DRAFT"),
                }

                print(f"  ✅ 게시 완료!")
                print(f"  🔗 URL: {result['url']}")
                return result

            except HttpError as e:
                # 429 Too Many Requests (Rate Limit) 처리
                if e.resp.status == 429:
                    if attempt < max_retries - 1:
                        print(f"  ⚠️ 429 에러 발생 (Rate Limit). {retry_delay}초 후 재시도 중... ({attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # 지수 백오프
                        continue
                    else:
                        print(f"  ❌ 최대 재시도 횟수를 초과했습니다.")
                        raise
                else:
                    print(f"  ❌ Blogger API 오류: {e}")
                    raise
            except Exception as e:
                print(f"  ❌ 게시 중 예외 발생: {e}")
                raise

    def get_blog_info(self) -> dict:
        """블로그 기본 정보를 가져옵니다."""
        try:
            blog = self.service.blogs().get(blogId=self.blog_id).execute()
            return {
                "name": blog.get("name"),
                "url": blog.get("url"),
                "posts_count": blog.get("posts", {}).get("totalItems", 0),
            }
        except Exception as e:
            print(f"  ❌ 블로그 정보 조회 오류: {e}")
            return None
