import cv2
import dlib

# Dlib의 얼굴 탐지기 및 랜드마크 모델 로드
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

# 웹캠 캡처
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # 흑백 변환
    faces = detector(gray)  # 얼굴 탐지

    for face in faces:
        landmarks = predictor(gray, face)

        # 눈 주변 랜드마크 그리기 (왼쪽 눈: 36~41, 오른쪽 눈: 42~47)
        for i in range(36, 48):
            x = landmarks.part(i).x
            y = landmarks.part(i).y
            cv2.circle(frame, (x, y), 2, (255, 0, 0), -1)

    cv2.imshow("Eye Tracking", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
