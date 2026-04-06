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
            # 헤더 반영
            headers = ["키워드", "제목", "메타설명", "태그", "본문링크", "이미지 프롬프트", "예약시간", "승인", "비고"]
            new_data.append(headers)
            continue
            
        if len(row) >= 11:
            # 본문미리보기(idx 4), 썸네일링크(idx 5)가 포함된 구 포맷
            new_row = row[:4] + row[6:11]
            new_data.append(new_row)
        else:
            # 이미 포맷이 변경되었거나 짧은 경우
            new_row = row[:9]
            while len(new_row) < 9:
                new_row.append("")
            new_data.append(new_row)

    # 시트 비우고 다시 쓰기
    ws.clear()
    ws.update("A1", new_data)
    
    # 행 높이 21로 고정
    sheet_id = ws.id
    sm.spreadsheet.batch_update({
        "requests": [{
            "updateDimensionProperties": {
                "range": {"sheetId": sheet_id, "dimension": "ROWS", "startIndex": 0, "endIndex": max(100, len(new_data) + 50)},
                "properties": {"pixelSize": 21},
                "fields": "pixelSize"
            }
        }]
    })
    
    print(f"동기화 완료! 총 {len(new_data)}개 행 업데이트.")

if __name__ == "__main__":
    sync_columns()
