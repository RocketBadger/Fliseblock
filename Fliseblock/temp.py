import cv2

cam = cv2.VideoCapture(-1)
cam.set(cv2.CAP_PROP_FRAME_WIDTH , 352);
cam.set(cv2.CAP_PROP_FRAME_HEIGHT , 288);
while True:
    ret, frame = cam.read()
    print(ret, frame)