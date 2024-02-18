import cv2
b_l_threhold - (100, 100, 100)
b_h_threhold = (150,255, 255)
g_l_threhold= (30,80,80)
g_h_threhold= (90,255, 255)
r_I_threhold = (-30, 100, 100)
r_h_threhold- (30, 255, 255)
cap =cv2.VideoCapture(0)
cap.set(cV2.CAP_PROP_FRAME_WIDTH,320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT,240)
if not cap, isOpened():
  print("cap open fai led")
  exit()

while True:
  ret, img = cap.read()
  if not ret:
    print ("Can't read cap")
    break
  hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
  g_mask - cv2. inRange(hsv_ img, g_I_threhold, g_h_threhold)
  b_mask=cv2. inRange(hsv_img, b_l_threhold, b_h_threhold)
  r_mask = cv2,inRange(hsv_img, r_I_threhold, r_h_threhold)
  blue_img = cv2.bitwise_and(img, img, mask=b_mask)
  green_img= cv2.bitwise_and(img, img, mask=g_mask)
  red_ing - cv2.bitwise_and(inig, ing, mask=r_mask)
  cv2.imshow('IMG',img)
  cv2.imshow("BLUE', blue_img)
  cv2. imshow('GREEN', green_img)
  cv2.imshow('RED', red_img)
  if cv2.waitkey(1) == ord("q'):
    break.
  if cv2.waitKey(1) == ord('c'):
    img_captured = cv2.imwrite(' img_captured.png*, img)
    img_captured = cv2.imwrite("blue_captured.png', blue_img)
    img_captured = cv2.imwrite('green_captured.png*, green_ing)
    img_captured = cv2.imwrite('red_captured.png', red_img)
cv2.destroyÅllWindows()
