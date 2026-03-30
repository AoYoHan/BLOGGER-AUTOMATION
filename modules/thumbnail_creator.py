"""
썸네일 합성 모듈
AI 생성 이미지 위에 텍스트를 오버레이하여 블로그 썸네일을 만듭니다.
"""
import io
import os
import sys
import textwrap

from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _find_korean_font() -> str:
    """시스템에 설치된 한글 폰트를 찾습니다."""
    # Windows 한글 폰트 경로들
    font_paths = [
        "C:/Windows/Fonts/malgun.ttf",       # 맑은 고딕
        "C:/Windows/Fonts/NanumGothic.ttf",   # 나눔고딕
        "C:/Windows/Fonts/NanumGothicBold.ttf",
        "C:/Windows/Fonts/gulim.ttc",          # 굴림
        "C:/Windows/Fonts/batang.ttc",         # 바탕
        # Linux
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        # macOS
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    ]
    for path in font_paths:
        if os.path.exists(path):
            return path
    return None


def create_thumbnail(image_data: bytes, title: str,
                     brand_text: str = "", overlay_opacity: int = 160) -> bytes:
    """
    AI 생성 이미지 위에 제목 텍스트를 합성하여 썸네일을 만듭니다.
    
    Args:
        image_data: 원본 이미지 바이너리 데이터
        title: 오버레이할 제목 텍스트
        brand_text: 브랜드명 (우하단 표시, 선택)
        overlay_opacity: 오버레이 투명도 (0~255)
    
    Returns:
        bytes: 완성된 썸네일 이미지 바이너리
    """
    if not image_data:
        print("  ⚠️ 이미지 데이터 없음, 썸네일 생성 건너뜀")
        return None

    try:
        # 원본 이미지 로드
        img = Image.open(io.BytesIO(image_data)).convert("RGBA")
        img = img.resize((1200, 630), Image.Resampling.LANCZOS)

        # 반투명 그라데이션 오버레이 생성
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw_overlay = ImageDraw.Draw(overlay)

        # 하단부에 그라데이션 오버레이
        for y in range(img.height // 3, img.height):
            progress = (y - img.height // 3) / (img.height * 2 // 3)
            alpha = int(overlay_opacity * progress)
            draw_overlay.line([(0, y), (img.width, y)], fill=(0, 0, 0, alpha))

        img = Image.alpha_composite(img, overlay)

        # 텍스트 그리기
        draw = ImageDraw.Draw(img)

        # 한글 폰트 찾기
        font_path = _find_korean_font()
        if font_path:
            title_font = ImageFont.truetype(font_path, 52)
            brand_font = ImageFont.truetype(font_path, 24)
        else:
            print("  ⚠️ 한글 폰트를 찾을 수 없어 기본 폰트를 사용합니다.")
            title_font = ImageFont.load_default()
            brand_font = ImageFont.load_default()

        # 제목 텍스트 줄바꿈 처리
        wrapped_title = textwrap.fill(title, width=20)
        lines = wrapped_title.split("\n")

        # 제목 위치 계산 (하단 중앙)
        y_position = img.height - 80 - (len(lines) * 60)
        for line in lines:
            # 텍스트 가운데 정렬
            bbox = draw.textbbox((0, 0), line, font=title_font)
            text_width = bbox[2] - bbox[0]
            x_position = (img.width - text_width) // 2

            # 그림자 효과
            draw.text((x_position + 2, y_position + 2), line, font=title_font, fill=(0, 0, 0, 200))
            # 본 텍스트
            draw.text((x_position, y_position), line, font=title_font, fill=(255, 255, 255, 255))
            y_position += 60

        # 브랜드 텍스트 (우하단)
        if brand_text:
            bbox = draw.textbbox((0, 0), brand_text, font=brand_font)
            bw = bbox[2] - bbox[0]
            draw.text((img.width - bw - 30, img.height - 50), brand_text,
                       font=brand_font, fill=(255, 255, 255, 180))

        # 바이너리로 변환
        img_rgb = img.convert("RGB")
        buffer = io.BytesIO()
        img_rgb.save(buffer, format="JPEG", quality=90)
        result = buffer.getvalue()

        print(f"  🖼️ 썸네일 생성 완료 ({len(result) // 1024}KB)")
        return result

    except Exception as e:
        print(f"  ❌ 썸네일 생성 오류: {e}")
        return image_data  # 실패 시 원본 반환
