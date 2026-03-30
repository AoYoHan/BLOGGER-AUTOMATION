"""
Google OAuth 2.0 인증 헬퍼
모든 Google API (Sheets, Drive, Blogger)에 공통으로 사용됩니다.
"""
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config.settings import CREDENTIALS_FILE, TOKEN_FILE, SCOPES


def get_google_credentials() -> Credentials:
    """
    Google OAuth 2.0 인증을 수행하고 Credentials 객체를 반환합니다.
    첫 실행 시 브라우저에서 로그인 후 토큰이 저장됩니다.
    이후 실행에서는 저장된 토큰을 재사용합니다.
    """
    creds = None

    # 저장된 토큰이 있으면 로드
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # 토큰이 없거나 만료된 경우
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 토큰 갱신 중...")
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"❌ credentials.json이 없습니다!\n"
                    f"   경로: {CREDENTIALS_FILE}\n"
                    f"   Google Cloud Console에서 OAuth 2.0 클라이언트 ID를 생성하고\n"
                    f"   JSON 파일을 config/ 폴더에 저장하세요."
                )
            print("🔐 브라우저에서 Google 계정 로그인을 진행해주세요...")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            print("✅ 인증 성공!")

        # 토큰 저장
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
            print(f"💾 토큰 저장됨: {TOKEN_FILE}")

    return creds
