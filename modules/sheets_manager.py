"""
Google Sheets 연동 모듈
메인 대시보드 역할: 키워드 관리, 초안 검토, 게시 현황 추적
"""
import os
import sys

import gspread

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config.settings import (
    SPREADSHEET_ID,
    SHEET_KEYWORDS,
    SHEET_DRAFTS,
    SHEET_PUBLISHED,
    STATUS_WAITING,
    STATUS_RESEARCHING,
    STATUS_GENERATING,
    STATUS_REVIEW,
    STATUS_APPROVED,
    STATUS_PUBLISHED,
    STATUS_ERROR,
)
from modules.google_auth import get_google_credentials


class SheetsManager:
    """Google Sheets 대시보드 관리자"""

    def __init__(self):
        creds = get_google_credentials()
        self.gc = gspread.authorize(creds)
        self.spreadsheet = self.gc.open_by_key(SPREADSHEET_ID)
        print(f"📊 Google Sheets 연결됨: {self.spreadsheet.title}")

    # ──────────────────────────────────────────
    #  시트 초기화 (최초 1회)
    # ──────────────────────────────────────────
    def initialize_sheets(self):
        """스프레드시트에 필요한 시트들이 없으면 생성합니다."""
        existing_sheets = [ws.title for ws in self.spreadsheet.worksheets()]

        # 시트 1: 키워드관리
        headers_keywords = [["키워드", "톤", "색상", "상태", "연관키워드", "검색의도", "SEO점수"]]
        if SHEET_KEYWORDS not in existing_sheets:
            ws = self.spreadsheet.add_worksheet(title=SHEET_KEYWORDS, rows=100, cols=10)
            print(f"  ✅ '{SHEET_KEYWORDS}' 시트 생성됨")
        else:
            ws = self.spreadsheet.worksheet(SHEET_KEYWORDS)
        
        ws.update("A1:G1", headers_keywords)
        ws.format("A1:G1", {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.85, "green": 0.92, "blue": 1.0}})

        # 시트 2: 초안검토
        headers_drafts = [["키워드", "제목", "메타설명", "본문링크", "이미지 프롬프트", "예약시간", "승인", "비고"]]
        if SHEET_DRAFTS not in existing_sheets:
            ws = self.spreadsheet.add_worksheet(title=SHEET_DRAFTS, rows=100, cols=8)

            print(f"  ✅ '{SHEET_DRAFTS}' 시트 생성됨")
        else:
            ws = self.spreadsheet.worksheet(SHEET_DRAFTS)
        
        ws.update("A1:H1", headers_drafts)
        ws.format("A1:H1", {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.9, "green": 1.0, "blue": 0.85}})

        # 행 높이 21로 고정
        sheet_id = ws.id
        body = {
            "requests": [
                {
                    "updateDimensionProperties": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "ROWS",
                            "startIndex": 0,
                            "endIndex": 1000
                        },
                        "properties": {
                            "pixelSize": 21
                        },
                        "fields": "pixelSize"
                    }
                }
            ]
        }
        self.spreadsheet.batch_update(body)


        # 시트 3: 게시현황
        headers_published = [["키워드", "제목", "게시일", "포스트URL", "이미지폴더", "상태", "색인결과"]]
        if SHEET_PUBLISHED not in existing_sheets:
            ws = self.spreadsheet.add_worksheet(title=SHEET_PUBLISHED, rows=100, cols=8)
            print(f"  ✅ '{SHEET_PUBLISHED}' 시트 생성됨")
        else:
            ws = self.spreadsheet.worksheet(SHEET_PUBLISHED)
        
        ws.update("A1:G1", headers_published)
        ws.format("A1:G1", {"textFormat": {"bold": True}, "backgroundColor": {"red": 1.0, "green": 0.93, "blue": 0.85}})

        print("📋 시트 초기화 완료!")

    # ──────────────────────────────────────────
    #  키워드관리 시트 조작
    # ──────────────────────────────────────────
    def get_pending_keywords(self) -> list[dict]:
        """'⏳대기' 상태인 키워드 목록을 가져옵니다."""
        ws = self.spreadsheet.worksheet(SHEET_KEYWORDS)
        records = ws.get_all_records()
        pending = []
        for i, row in enumerate(records, start=2):  # 2행부터 (1행은 헤더)
            status = str(row.get("상태", "")).strip()
            keyword = str(row.get("키워드", "")).strip()
            if keyword and (status == STATUS_WAITING or status == "" or status is None):
                pending.append({
                    "row": i,
                    "keyword": keyword,
                    "tone": str(row.get("톤", "")).strip() or "전문적이면서 친근한",
                    "color": str(row.get("색상", "")).strip() or "#3d94f6",
                    "related_keywords": str(row.get("연관키워드", "")).strip(),
                    "search_intent": str(row.get("검색의도", "")).strip(),
                })
        return pending

    def update_keyword_status(self, row: int, status: str, related: str = "", intent: str = "", seo_score: str = ""):
        """키워드관리 시트의 상태를 업데이트합니다."""
        ws = self.spreadsheet.worksheet(SHEET_KEYWORDS)
        updates = {"D" + str(row): status}
        if related:
            updates["E" + str(row)] = related
        if intent:
            updates["F" + str(row)] = intent
        if seo_score:
            updates["G" + str(row)] = seo_score
        for cell, value in updates.items():
            ws.update_acell(cell, value)

    # ──────────────────────────────────────────
    #  초안검토 시트 조작
    # ──────────────────────────────────────────
    def add_draft(self, keyword: str, title: str, meta: str,
                  doc_url: str, image_prompts: str = "", 
                  publish_time: str = "", approval: str = "대기"):

        """초안검토 시트에 새 초안을 추가합니다."""
        ws = self.spreadsheet.worksheet(SHEET_DRAFTS)
        # 이미 같은 키워드가 있으면 업데이트
        existing = ws.get_all_records()
        row_idx = len(existing) + 2
        for i, row in enumerate(existing, start=2):
            if str(row.get("키워드", "")).strip() == keyword:
                ws.update(f"A{i}:H{i}", [[keyword, title, meta, doc_url, image_prompts, publish_time, approval, ""]])
                row_idx = i
                break
        else:
            # 새 행 추가 (loop 안에서 안 걸린 경우)
            ws.append_row([keyword, title, meta, doc_url, image_prompts, publish_time, approval, ""])
            
        # 행 높이 21로 고정
        sheet_id = ws.id
        self.spreadsheet.batch_update({
            "requests": [{
                "updateDimensionProperties": {
                    "range": {"sheetId": sheet_id, "dimension": "ROWS", "startIndex": row_idx - 1, "endIndex": row_idx},
                    "properties": {"pixelSize": 21},
                    "fields": "pixelSize"
                }
            }]
        })
        return row_idx


    def get_approved_drafts(self) -> list[dict]:
        """승인(✅)된 초안 목록을 가져옵니다."""
        ws = self.spreadsheet.worksheet(SHEET_DRAFTS)
        records = ws.get_all_records()
        approved = []
        for i, row in enumerate(records, start=2):
            approval = str(row.get("승인", "")).strip()
            if approval == "승인" or approval == "✅":
                approved.append({
                    "row": i,
                    "keyword": str(row.get("키워드", "")).strip(),
                    "title": str(row.get("제목", "")).strip(),
                    "meta_description": str(row.get("메타설명", "")).strip(),

                    "doc_url": str(row.get("본문링크", "")).strip(),
                    "예약시간": str(row.get("예약시간", "")).strip(),
                })
        return approved

    def mark_draft_published(self, row: int):
        """초안검토 시트에서 게시 완료 표시"""
        ws = self.spreadsheet.worksheet(SHEET_DRAFTS)
        ws.update_acell(f"F{row}", "🚀게시됨")

    # ──────────────────────────────────────────
    #  게시현황 시트 조작
    # ──────────────────────────────────────────
    def add_published_record(self, keyword: str, title: str, post_url: str,
                              image_folder_url: str, published_date: str, indexing_status: str = "대기"):
        """게시현황 시트에 게시 결과를 기록합니다."""
        ws = self.spreadsheet.worksheet(SHEET_PUBLISHED)
        ws.append_row([keyword, title, published_date, post_url, image_folder_url, STATUS_PUBLISHED, indexing_status])
