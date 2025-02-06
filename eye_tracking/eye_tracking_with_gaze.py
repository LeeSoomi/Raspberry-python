import cv2
import dlib

# Dlib 모델 로드
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

# 웹캠 초기화
cap = cv2.VideoCapture(0)

def calculate_eye_center(eye_points):
    """눈 중심 좌표 계산"""
    x_coords = [point.x for point in eye_points]
    y_coords = [point.y for point in eye_points]
    center_x = int(sum(x_coords) / len(x_coords))
    center_y = int(sum(y_coords) / len(y_coords))
    return (center_x, center_y)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # 흑백 변환
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 얼굴 감지
    faces = detector(gray)
    for face in faces:
        landmarks = predictor(gray, face)

        # 왼쪽 및 오른쪽 눈의 랜드마크
        left_eye_points = landmarks.parts()[36:42]
        right_eye_points = landmarks.parts()[42:48]

        # 눈 중심 계산
        left_eye_center = calculate_eye_center(left_eye_points)
        right_eye_center = calculate_eye_center(right_eye_points)

        # 눈 중심을 표시
        cv2.circle(frame, left_eye_center, 3, (0, 255, 0), -1)
        cv2.circle(frame, right_eye_center, 3, (0, 255, 0), -1)

        # 눈 랜드마크 표시
        for point in left_eye_points + right_eye_points:
            cv2.circle(frame, (point.x, point.y), 2, (255, 0, 0), -1)

    # 화면 출력
    cv2.imshow("Eye Tracking with Gaze", frame)

    # 'q'를 누르면 종료
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
