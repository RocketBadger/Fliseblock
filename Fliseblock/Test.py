from Fliseblock import Fliseblock
import time
from Tests import *
from send_cam import stream_camera

robbie = Fliseblock()

print('Streaming Camera')
stream_camera()
print('Sleeping 5 seconds')
time.sleep(5)
print('Running camServosTest')
camServosTest(robbie)
