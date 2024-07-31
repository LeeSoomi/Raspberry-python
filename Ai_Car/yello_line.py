import cv2
import motor_module as motor
import RPi.GPIO as GPIO
import time

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

Frame_Width = 640
Frame_Height = 480
camera = cv2.VideoCapture(0)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, Frame_Width)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, Frame_Height)

# 노란색 범위 설정 (HSV 색공간에서)
yellow_lower = (20, 100, 100)
yellow_upper = (30, 255, 255)

# 빨간색 범위 설정 (HSV 색공간에서)
red_lower1 = (0, 100, 100)
red_upper1 = (5, 255, 255)
red_lower2 = (170, 100, 100)
red_upper2 = (180, 255, 255)

try:
    while True:
        _, frame = camera.read()
        frame = cv2.GaussianBlur(frame, (11, 11), 1)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # 노란색 마스크 생성
        yellow_mask = cv2.inRange(hsv, yellow_lower, yellow_upper)
        yellow_mask = cv2.erode(yellow_mask, None, iterations=2)
        yellow_mask = cv2.dilate(yellow_mask, None, iterations=2)

        # 빨간색 마스크 생성
        red_mask1 = cv2.inRange(hsv, red_lower1, red_upper1)
        red_mask2 = cv2.inRange(hsv, red_lower2, red_upper2)
        red_mask = cv2.addWeighted(red_mask1, 1.0, red_mask2, 1.0, 0.0)
        red_mask = cv2.erode(red_mask, None, iterations=2)
        red_mask = cv2.dilate(red_mask, None, iterations=2)

        # 빨간색이 감지되면 모터 정지
        if cv2.countNonZero(red_mask) > 0:
            motor.stop()
            continue

        # 노란색 선 추적
        contours, _ = cv2.findContours(yellow_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        center = None
        if len(contours) > 0:
            c = max(contours, key=cv2.contourArea)
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            M = cv2.moments(c)

            try:
                center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
                cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 255), 2)
                cv2.circle(frame, center, 5, (0, 0, 255), -1)
                if radius > 5:
                    if center[0] > Frame_Width / 2 + 55:
                        motor.turnRight()
                    elif center[0] < Frame_Width / 2 - 55:
                        motor.turnLeft()
                    else:
                        motor.forward_1()
                else:
                    motor.brake()
            except:
                pass
        else:
            motor.stop()

        cv2.imshow("Frame", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
finally:
    motor.cleanup()
    camera.release()
    cv2.destroyAllWindows()
