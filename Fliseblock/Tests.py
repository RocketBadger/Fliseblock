from Fliseblock import Fliseblock
import time

# robot = Fliseblock()

def camServosTest(robot):
    Fliseblock.camInit(robot)
    time.sleep(0.5)
    Fliseblock.camUp(robot, 500)
    time.sleep(0.5)
    Fliseblock.camDown(robot, 500)    
    time.sleep(0.5)
    Fliseblock.camLeft(robot, 500)
    time.sleep(0.5)
    Fliseblock.camRight(robot, 1000)
    time.sleep(0.5)
    Fliseblock.camLeft(robot, 500)
    
def wheelControlTest(robot):
    Fliseblock.wheel_control_forwards(robot, 500)
    Fliseblock.wheel_control_backwards(robot, 500)