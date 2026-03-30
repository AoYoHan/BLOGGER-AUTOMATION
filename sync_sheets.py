import os
import sys

# 프로젝트 루트를 패스에 추가
sys.path.insert(0, os.getcwd())

from modules.sheets_manager import SheetsManager

def sync_columns():
    sm = SheetsManager()
    ws = sm.spreadsheet.worksheet("초안검토")
    data = ws.get_all_values()
    
    if not data:
        print("시트가 비어있습니다.")
        return

    print(f"현재 헤더 ({len(data[0])}개): {data[0]}")
    
    # 0-indexed: 8번 컬럼(본문HTML)을 삭제하고 나머지를 당김
    # 데이터가 12개 이상인 경우만 처리
    new_data = []
    for i, row in enumerate(data):
        if i == 0:
            # 헤더는 이미 initialize_sheets에서 업데이트되었을 것이지만 다시 확인
            headers = ["키워드", "제목", "메타설명", "태그", "본문미리보기", "썸네일링크", "본문링크", "이미지 프롬프트", "예약시간", "승인", "비고"]
            new_data.append(headers)
            continue
            
        if len(row) >= 12:
            # 본문HTML(idx 8)이 포함된 구 포맷이라고 가정
            new_row = row[:8] + row[9:12] # idx 9, 10, 11 (예약시간, 승인, 비고)을 8, 9, 10으로 당김
            new_data.append(new_row)
        else:
            # 이미 11개 이하인 경우 그대로 유지 또는 길이 맞춤
            new_row = row[:11]
            while len(new_row) < 11:
                new_row.append("")
            new_data.append(new_row)

    # 시트 비우고 다시 쓰기 (주의: 포맷팅이 날아갈 수 있음, 하지만 update_acell 등은 행/열 인덱스 기반이라 동기화가 필수적임)
    ws.clear()
    ws.update("A1", new_data)
    print(f"동기화 완료! 총 {len(new_data)}개 행 업데이트.")

if __name__ == "__main__":
    sync_columns()
