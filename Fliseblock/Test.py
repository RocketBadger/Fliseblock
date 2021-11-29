from Fliseblock import Fliseblock
from Tests import *
import serial
# from opencv_openmv_bridge import Camera
# Camera.send_image()
from get_line_data import Camera

robbie = Fliseblock()

Fliseblock.camInitPos(robbie)


Camera.get_lines()
i  = 0
while True:
    i = i + 1
    