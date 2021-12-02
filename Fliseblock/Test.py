from Fliseblock import Fliseblock
from Tests import *
# from opencv_openmv_bridge import Camera

from line_data import Camera

robbie = Fliseblock()

Fliseblock.camInitPos(robbie)

# Camera.send_image()
Camera.get_lines()
i  = 0
while True:
    i = i + 1
    