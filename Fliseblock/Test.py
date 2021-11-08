from Fliseblock import Fliseblock
import time
from Tests import *
from send_cam import stream_camera

robbie = Fliseblock()

print('Streaming Camera')
stream_camera()
print('Sleeping 2 seconds')
time.sleep(2)
print('Running camServosTest')
camServosTest(robbie)

print('Sleeping 2 seconds')
time.sleep(2)
print('Running camServosTest')
camServosTest(robbie)

print('Sleeping 2 seconds')
time.sleep(2)
print('Running wheelControlTest')
wheelControlTest(robbie)