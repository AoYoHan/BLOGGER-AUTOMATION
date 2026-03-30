"""
전역 설정 모듈
환경 변수 또는 .env 파일에서 설정값을 로드합니다.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ─── Gemini API ───────────────────────────────────────────
# 단일 키(GEMINI_API_KEY) 또는 복수 키(GEMINI_API_KEYS, 콤마로 구분) 모두 지원
_api_keys_str = os.getenv("GEMINI_API_KEYS") or os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")
GEMINI_API_KEYS = [k.strip() for k in _api_keys_str.split(",") if k.strip()]
if not GEMINI_API_KEYS:
    GEMINI_API_KEYS = ["YOUR_GEMINI_API_KEY"]

_current_key_idx = 0
GEMINI_API_KEY = GEMINI_API_KEYS[_current_key_idx] # 하위 호환성을 위해 유지

def get_current_api_key() -> str:
    global _current_key_idx
    return GEMINI_API_KEYS[_current_key_idx]

def switch_api_key() -> str:
    global _current_key_idx
    _current_key_idx = (_current_key_idx + 1) % len(GEMINI_API_KEYS)
    new_key = GEMINI_API_KEYS[_current_key_idx]
    
    # 힌트용 키 출력 (앞 4자리)
    key_hint = new_key[:4] + "***" if len(new_key) > 4 else "***"
    print(f"  🔄 API 키 전환 -> [{_current_key_idx + 1}/{len(GEMINI_API_KEYS)}] {key_hint}")
    return new_key

def get_total_api_keys() -> int:
    return len(GEMINI_API_KEYS)

# ─── Google OAuth 2.0 ────────────────────────────────────
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "credentials.json")
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "token.json")

# 필요한 OAuth 스코프
SCOPES = [
    "https://www.googleapis.com/auth/blogger",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/indexing",
]

# ─── Blogger ─────────────────────────────────────────────
BLOG_ID = os.getenv("BLOG_ID", "YOUR_BLOG_ID")

# ─── Google Sheets ───────────────────────────────────────
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "YOUR_SPREADSHEET_ID")

# 시트 이름
SHEET_KEYWORDS = "키워드관리"
SHEET_DRAFTS = "초안검토"
SHEET_PUBLISHED = "게시현황"

# ─── Google Drive ────────────────────────────────────────
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID", "YOUR_DRIVE_FOLDER_ID")

# ─── 콘텐츠 생성 설정 ───────────────────────────────────
DEFAULT_TONE = "전문적이면서 친근한"
TARGET_YEAR = "2026"
MIN_WORD_COUNT = 1000
TARGET_KEYWORD_DENSITY = 0.02  # 2%
MIN_SEO_SCORE = 70
DELAY_BETWEEN_KEYWORDS = 30
DELAY_BEFORE_API_CALL = 3

# ─── 상태값 ──────────────────────────────────────────────
STATUS_WAITING = "⏳대기"
STATUS_PAUSED = "⏸️보류"
STATUS_RESEARCHING = "🔍리서치중"
STATUS_GENERATING = "✍️생성중"
STATUS_REVIEW = "📝검토대기"
STATUS_APPROVED = "✅승인"
STATUS_PUBLISHED = "✅게시완료"
STATUS_ERROR = "❌오류"
