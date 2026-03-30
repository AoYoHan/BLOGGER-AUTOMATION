"""
Google Drive 업로드 모듈
생성된 이미지를 Google Drive에 업로드하고 공유 링크를 반환합니다.
"""
import io
import os
import sys

from typing import Optional, List, Dict
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config.settings import DRIVE_FOLDER_ID
from modules.google_auth import get_google_credentials


class DriveManager:
    """Google Drive 이미지 업로드 관리자"""

    def __init__(self):
        creds = get_google_credentials()
        self.service = build("drive", "v3", credentials=creds)
        self.base_folder_id = DRIVE_FOLDER_ID
        print(f"📁 Google Drive 연결됨")

    def create_subfolder(self, folder_name: str) -> str:
        """
        base_folder 안에 하위 폴더를 생성합니다.
        이미 존재하면 기존 폴더 ID를 반환합니다.
        """
        # 기존 폴더 검색
        query = (
            f"name='{folder_name}' and "
            f"'{self.base_folder_id}' in parents and "
            f"mimeType='application/vnd.google-apps.folder' and "
            f"trashed=false"
        )
        results = self.service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get("files", [])

        if files:
            return files[0]["id"]

        # 새 폴더 생성
        metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [self.base_folder_id],
        }
        folder = self.service.files().create(body=metadata, fields="id").execute()
        print(f"  📂 폴더 생성: {folder_name}")
        return folder["id"]

    def upload_text_content(self, title: str, html_content: str, folder_id: str) -> dict:
        """
        블로그 본문을 Google Doc으로 변환하여 업로드합니다.
        """
        metadata = {
            "name": title,
            "mimeType": "application/vnd.google-apps.document",
            "parents": [folder_id],
        }

        media = MediaIoBaseUpload(
            io.BytesIO(html_content.encode("utf-8")),
            mimetype="text/html",
            resumable=True,
        )

        file = self.service.files().create(
            body=metadata, media_body=media, fields="id, webViewLink"
        ).execute()

        self.service.permissions().create(
            fileId=file["id"],
            body={"type": "anyone", "role": "reader"},
        ).execute()

        print(f"  📝 초안 문서 생성됨: {file.get('webViewLink')}")
        return {
            "id": file["id"],
            "url": file.get("webViewLink"),
        }

    def upload_image(self, image_data: bytes, filename: str, folder_id: str,
                     mime_type: str = "image/jpeg") -> dict:
        """
        이미지를 Google Drive에 업로드하고 공유 링크를 반환합니다.
        """
        if not image_data:
            return {"id": None, "url": None}

        metadata = {
            "name": filename,
            "parents": [folder_id],
        }

        media = MediaIoBaseUpload(
            io.BytesIO(image_data),
            mimetype=mime_type,
            resumable=True,
        )

        file = self.service.files().create(
            body=metadata, media_body=media, fields="id, webViewLink"
        ).execute()

        # 공개 읽기 권한 설정
        self.service.permissions().create(
            fileId=file["id"],
            body={"type": "anyone", "role": "reader"},
        ).execute()

        # 직접 접근 가능한 URL 생성
        direct_url = f"https://drive.google.com/uc?export=view&id={file['id']}"

        print(f"  ☁️ 업로드: {filename} → {direct_url}")
        return {
            "id": file["id"],
            "url": direct_url,
            "web_link": file.get("webViewLink", ""),
        }


    def upload_post_images(self, keyword: str, images: dict, content_html: Optional[str] = None) -> dict:
        """
        포스트의 모든 이미지와 본문 문서를 Drive에 업로드합니다.
        
        Args:
            keyword: 키워드 (폴더명으로 사용)
            images: image_generator.generate_images_for_post()의 결과
            content_html: 블로그 본문 HTML (제공 시 문서로 업로드)
        
        Returns:
            dict: {
                "folder_id": str,
                "folder_url": str,
                "hero_url": str,
                "thumbnail_url": str,
                "body_urls": list[str],
                "doc_url": str,
            }
        """
        print(f"\n☁️ Google Drive 업로드: '{keyword}'")

        # 키워드별 하위 폴더 생성
        safe_name = keyword.replace(" ", "_").replace("/", "_")[:50]
        folder_id = self.create_subfolder(f"blog_{safe_name}")
        folder_url = f"https://drive.google.com/drive/folders/{folder_id}"

        result = {
            "folder_id": folder_id,
            "folder_url": folder_url,
            "hero_url": None,
            "thumbnail_url": None,
            "body_urls": [],
            "doc_url": None,
        }

        # 0. 본문 문서 업로드
        if content_html:
            doc = self.upload_text_content(f"{keyword}_초안", content_html, folder_id)
            result["doc_url"] = doc["url"]

        # 1. 대표 이미지 업로드
        if images.get("hero"):
            hero = self.upload_image(images["hero"], f"{safe_name}_hero.jpg", folder_id)
            result["hero_url"] = hero["url"]

        # 썸네일 업로드
        if images.get("thumbnail"):
            thumb = self.upload_image(images["thumbnail"], f"{safe_name}_thumbnail.jpg", folder_id)
            result["thumbnail_url"] = thumb["url"]

        # 본문 이미지 업로드
        for i, img in enumerate(images.get("body_images", []), 1):
            uploaded = self.upload_image(img["data"], f"{safe_name}_body_{i}.jpg", folder_id)
            result["body_urls"].append({
                "topic": img["topic"],
                "url": uploaded["url"],
            })

        total = (1 if result["doc_url"] else 0) + (1 if result["hero_url"] else 0) + (1 if result["thumbnail_url"] else 0) + len(result["body_urls"])
        print(f"  🎉 총 {total}개 파일 업로드 완료!")
        return result
