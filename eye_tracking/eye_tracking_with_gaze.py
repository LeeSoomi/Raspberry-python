import cv2
import dlib

# Dlib의 얼굴 검출기와 랜드마크 예측기 로드
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

# 웹캠 캡처
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # 흑백 변환
    faces = detector(gray)  # 얼굴 검출
    
    for face in faces:
        landmarks = predictor(gray, face)
        
        # 왼쪽, 오른쪽 눈 좌표 추출
        left_eye = landmarks.parts()[36:42]  # 36~41번 점: 왼쪽 눈
        right_eye = landmarks.parts()[42:48]  # 42~47번 점: 오른쪽 눈

        # 눈 주변에 사각형 그리기
        for point in left_eye:
            cv2.circle(frame, (point.x, point.y), 2, (255, 0, 0), -1)
        for point in right_eye:
            cv2.circle(frame, (point.x, point.y), 2, (255, 0, 0), -1)
    
    cv2.imshow("Eye Tracking", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
