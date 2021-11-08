from Fliseblock import Fliseblock
import time
from Tests import *
from send_cam import stream_camera
from PID import PositionalPID

robbie = Fliseblock()

# print('Streaming Camera')
# stream_camera()
# print('Sleeping 2 seconds')
# time.sleep(2)
# print('Running camServosTest')
# camServosTest(robbie)
# print('Sleeping 2 seconds')
# time.sleep(2)
# print('Running camServosTest')
# camServosTest(robbie)
# print('Sleeping 2 seconds')
# time.sleep(2)
# print('Running wheelControlTest')
# wheelControlTest(robbie)

xservo_pid = PID.PositionalPID(1.1, 0.2, 0.8)
yservo_pid = PID.PositionalPID(0.8, 0.2, 0.8)
#Autopilot steering angle PID
Z_axis_pid = PID.PositionalPID(0.7, 0.00, 1.8)