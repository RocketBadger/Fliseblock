import threading
from Fliseblock import Fliseblock
import time
# from send_cam import stream_camera
from Tests import *
from Edge_detection import stream_camera_edged
from opencv_openmv_bridge import Camera

robbie = Fliseblock()

Fliseblock.camInitPos(robbie)


Camera.send_image()
while True:
    camServosTest(robbie)