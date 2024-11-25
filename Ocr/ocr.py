import cv2
import pytesseract
from PIL import Image
import pandas as pd

# Tesseract OCR 경로 설정 (Windows의 경우)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 이미지 파일 경로
image_path = r'C:\Users\sm759\Documents\KYC\captured_receipt.jpg'

# 이미지 로드 및 전처리
image = cv2.imread(image_path)
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # 흑백 변환
_, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)  # 이진화

# 텍스트 추출
text = pytesseract.image_to_string(thresh, lang='kor')  # 'lang=kor'로 한글 설정
print("추출된 텍스트:")
print(text)

# 추출된 텍스트를 줄 단위로 나누기
lines = text.split("\n")

# 데이터 정리 및 Excel 저장
data = {"항목": [], "가격": []}
for line in lines:
    parts = line.split()  # 공백 기준으로 나누기
    if len(parts) >= 2:  # 적어도 2개의 데이터가 있어야 함
        try:
            price = int(parts[-1].replace(",", ""))  # 마지막 항목을 가격으로 가정
            name = " ".join(parts[:-1])  # 나머지를 항목 이름으로 가정
            data["항목"].append(name)
            data["가격"].append(price)
        except ValueError:
            continue

# 데이터프레임 생성
df = pd.DataFrame(data)

# Excel 파일로 저장
excel_path = r'C:\Users\sm759\Documents\KYC\receipt_data.xlsx'
df.to_excel(excel_path, index=False, engine='openpyxl')
print(f"데이터가 Excel 파일로 저장되었습니다: {excel_path}")
