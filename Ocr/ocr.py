import cv2
import pytesseract
import pandas as pd
import re

# Tesseract 경로 설정
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 이미지 파일 경로
image_path = r'C:\Users\sm759\Documents\KYC\processed_receipt.jpg'

# 1. 이미지 로드 및 전처리
image = cv2.imread(image_path)
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # 흑백 변환
_, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)  # 이진화

# 텍스트 추출
text = pytesseract.image_to_string(thresh, lang='kor')

# 2. 데이터 정리
lines = text.split("\n")
items = []

# 패턴 정의
item_pattern = re.compile(r"(.+)\s+(\d+)\s+(\d+)\s+(\d+)")  # 항목명, 단가, 수량, 총금액
summary_pattern = re.compile(r"(\d+,\d+)")  # 합계 정보 추출

for line in lines:
    match = item_pattern.match(line)
    if match:
        name = match.group(1).strip()  # 항목명
        price = int(match.group(2).replace(",", ""))  # 단가
        quantity = int(match.group(3))  # 수량
        total = int(match.group(4).replace(",", ""))  # 총금액
        items.append({"항목": name, "단가": price, "수량": quantity, "총금액": total})

# 3. 합계 정보 추가
summary = {"구분": [], "금액": []}
for line in lines:
    if "합계" in line or "부가세" in line:
        amounts = summary_pattern.findall(line)
        if amounts:
            summary["구분"].append(line.strip())
            summary["금액"].append(amounts[-1].replace(",", ""))

# 4. DataFrame 생성
item_df = pd.DataFrame(items)
summary_df = pd.DataFrame(summary)

# Excel 저장 경로
excel_path = r'C:\Users\sm759\Documents\KYC\receipt_data_detailed.xlsx'

# Excel로 저장
with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
    item_df.to_excel(writer, sheet_name="항목별 데이터", index=False)
    summary_df.to_excel(writer, sheet_name="합계 정보", index=False)

print(f"영수증 데이터가 Excel로 저장되었습니다: {excel_path}")



코드 설명
이미지 전처리:

이미지를 흑백 변환 및 이진화 처리하여 OCR 성능을 높였습니다.
데이터 추출:

item_pattern 정규식을 사용해 항목명, 단가, 수량, 총금액을 추출합니다.
summary_pattern 정규식을 사용해 합계 정보(총합, 부가세 등)를 추출합니다.
DataFrame 생성:

항목별 데이터는 item_df에 저장합니다.
합계 정보는 summary_df에 저장합니다.
Excel 저장:

pandas.ExcelWriter를 사용하여 데이터를 여러 시트에 저장합니다.
실행 결과
항목별 데이터:

항목명, 단가, 수량, 총금액이 포함된 테이블이 Excel 파일의 "항목별 데이터" 시트에 저장됩니다.
합계 정보:

부가세 및 합계 정보가 "합계 정보" 시트에 저장됩니다.