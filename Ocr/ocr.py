import cv2
import pytesseract
from PIL import Image
import openpyxl

# Tesseract 경로 설정 (Tesseract이 설치된 경로)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 웹캠 열기
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("웹캠을 열 수 없습니다.")
    exit()

print("스페이스바를 눌러 사진을 촬영하세요.")
while True:
    ret, frame = cap.read()
    if not ret:
        print("프레임을 가져올 수 없습니다.")
        break

    cv2.imshow('Capture Image', frame)

    # 스페이스바를 누르면 촬영
    if cv2.waitKey(1) & 0xFF == ord(' '):
        image_path = 'captured_receipt.jpg'
        cv2.imwrite(image_path, frame)
        print(f"이미지가 {image_path}로 저장되었습니다.")
        break

# 웹캠 닫기
cap.release()
cv2.destroyAllWindows()

# OCR 처리
image = Image.open(image_path)
text = pytesseract.image_to_string(image, lang='eng')

# Excel 파일 생성 및 저장
wb = openpyxl.Workbook()
sheet = wb.active
sheet.title = "Receipt Data"

for i, line in enumerate(text.split('\n'), start=1):
    sheet.cell(row=i, column=1, value=line)

wb.save('receipt_data.xlsx')

print("작업이 완료되었습니다. receipt_data.xlsx 파일이 생성되었습니다.")
