from Fliseblock import Fliseblock
import time
# from send_cam import stream_camera
from Tests import *
from Edge_detection import stream_camera_edged
from opencv_openmv_bridge import Camera

# robbie = Fliseblock()

# Fliseblock.camInitPos(robbie)

# stream_camera_edged()
# stream_camera()
# print("camera stream started")
# time.sleep(10)
# camServosTest(robbie)
# sensorOpen()

while True:
    Camera.send_image()