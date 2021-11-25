from Fliseblock import Fliseblock
from Tests import *
import serial
# from opencv_openmv_bridge import Camera
# Camera.send_image()
from get_line_data import Camera

robbie = Fliseblock()

ser = serial.Serial('/dev/ttyACM0',115200)

Fliseblock.camInitPos(robbie)


Camera.get_lines()
i  = 0
while True:
    i = i + 1

    # print("waiting...")
    # if ser.in_waiting > 0:
        # ser.flushInput()
        # print("flushed input")
    # print(ser.read())
