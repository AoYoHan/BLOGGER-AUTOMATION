# ?? AI 블로그 자동 생성 시스템

Google Sheets에서 키워드만 입력하면 → AI가 SEO 최적화 글을 생성하고 → Google Blogger에 자동 게시하는 시스템입니다.

## ? 주요 기능

- **키워드 리서치**: Google Autocomplete + Gemini AI 분석 (연관키워드, 검색의도, 콘텐츠 방향)
- **AI 콘텐츠 생성**: Gemini API로 SEO 최적화된 2000자+ 블로그 글 자동 작성
- **AI 이미지 생성**: Pollinations.ai로 대표 이미지 + 본문 이미지 무료 생성
- **썸네일 합성**: 한글 텍스트 오버레이된 썸네일 자동 생성
- **SEO 점수 분석**: 11개 항목 자동 검증 (제목, 키워드 밀도, 구조 등)
- **Google Sheets UI**: 스프레드시트로 키워드 관리, 초안 검토, 승인까지 처리
- **Blogger 자동 게시**: 승인된 글만 Blogger API로 자동 게시

## ?? 사전 준비

### 1. Python 환경 설정

```bash
# Python 3.11+ 필요
pip install -r requirements.txt
```

### 2. Google Cloud 설정

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. **새 프로젝트 생성** 또는 기존 프로젝트 선택
3. **API 3개 활성화**:
   - `Blogger API v3`
   - `Google Sheets API`
   - `Google Drive API`
4. **OAuth 2.0 자격증명 생성**:
   - 사용자 인증 정보 → 사용자 인증 정보 만들기 → OAuth 클라이언트 ID
   - 애플리케이션 유형: **데스크톱 앱**
   - JSON 파일 다운로드 → `config/credentials.json`으로 저장

### 3. Gemini API 키

1. [Google AI Studio](https://aistudio.google.com/) 접속
2. API 키 발급
3. `.env` 파일에 설정

### 4. 환경 변수 설정

```bash
# .env.example을 복사하여 .env 파일 생성
copy .env.example .env
```

`.env` 파일을 열고 값을 입력하세요:

```env
GEMINI_API_KEY=your_actual_gemini_api_key
BLOG_ID=your_blog_id
SPREADSHEET_ID=your_google_sheets_id
DRIVE_FOLDER_ID=your_drive_folder_id
```

**값 찾는 방법:**
- **BLOG_ID**: Blogger 대시보드 URL에서 `blogID=` 뒤의 숫자
- **SPREADSHEET_ID**: Google Sheets URL에서 `/d/` 와 `/edit` 사이의 문자열
- **DRIVE_FOLDER_ID**: Google Drive 폴더 URL에서 `folders/` 뒤의 문자열

### 5. Google Sheets 준비

```bash
# 시트 자동 초기화 (3개 시트 자동 생성)
python main.py init
```           

1bjimb0UvlFGeONnUMRmkdGOSGqcczWvb

## ?? 사용법

### 전체 흐름

```
1. Sheets에 키워드 입력  →  2. 초안 생성  →  3. 검토/승인  →  4. 게시
```

### Step 1: 키워드 입력

Google Sheets의 **'키워드관리'** 시트에 키워드와 톤을 입력합니다:

| 키워드 | 톤 | 상태 |
|--------|-----|------|
| 파이썬 자동화 | 전문적 | ?대기 |
| AI 블로그 | 친근한 | ?대기 |

### Step 2: 초안 생성

```bash
python main.py generate
```

자동으로 처리됩니다:
- ? 키워드 리서치 (연관 키워드, 검색 의도 분석)
- ? AI 글 생성 (SEO 최적화 2000자+)
- ? AI 이미지 생성 (대표 + 본문 이미지)
- ? 썸네일 합성
- ? Google Drive에 이미지 업로드
- ? SEO 점수 분석

### Step 3: 검토 & 승인

**'초안검토'** 시트에서 결과를 확인합니다:
- 제목, 메타설명, 태그 확인
- 썸네일 링크 클릭하여 이미지 확인
- 마음에 들면 **'승인' 열에 ? 입력**

### Step 4: Blogger 게시

```bash
python main.py publish
```

승인(?)된 글만 자동으로 Blogger에 게시됩니다.

### 상태 확인

```bash
python main.py status
```

## ?? 프로젝트 구조

```
blogger-automation/
├── config/
│   ├── settings.py          # 전역 설정
│   ├── credentials.json     # Google OAuth (직접 배치)
│   └── token.json           # 자동 생성됨
├── modules/
│   ├── google_auth.py       # OAuth 인증
│   ├── sheets_manager.py    # Google Sheets 연동
│   ├── keyword_research.py  # 키워드 리서치
│   ├── content_generator.py # AI 글 생성
│   ├── image_generator.py   # AI 이미지 생성
│   ├── thumbnail_creator.py # 썸네일 합성
│   ├── drive_manager.py     # Google Drive 업로드
│   ├── seo_optimizer.py     # SEO 검증
│   └── blogger_publisher.py # Blogger 게시
├── main.py                  # 파이프라인 CLI
├── requirements.txt
├── .env.example
└── README.md
```

## ? 문제 해결

| 문제 | 해결 |
|------|------|
| `credentials.json 없음` | GCP에서 OAuth 클라이언트 ID 다운로드 |
| `토큰 만료` | `config/token.json` 삭제 후 재실행 |
| `이미지 생성 실패` | Pollinations.ai 서버 상태 확인 (무료라 간헐적 지연) |
| `Blogger 게시 오류` | BLOG_ID 확인 + Blogger API 활성화 여부 확인 |
