import threading
from Fliseblock import Fliseblock
import time
# from send_cam import stream_camera
from Tests import *
# from Edge_detection import stream_camera_edged
from opencv_openmv_bridge import Camera
import serial

robbie = Fliseblock()

ser = serial.Serial('/dev/ttyACM0',115200)

Fliseblock.camInitPos(robbie)


Camera.send_image()
i  = 0
while True:
    i = i + 1
    # print("waiting...")
    # if ser.in_waiting > 0:
        # ser.flushInput()
        # print("flushed input")
    # print(ser.read())
