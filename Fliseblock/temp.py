import cv2

cam = cv2.VideoCapture(0)
print(cam.isOpened())
while True:
    ret, frame = cam.read()
    print(ret, frame)