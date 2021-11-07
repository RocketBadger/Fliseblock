from Fliseblock import Fliseblock
import time

# robot = Fliseblock()

def camServosTest(robot):
    Fliseblock.camInit(robot)
    time.sleep(1)
    Fliseblock.camUp(robot, 200)
    time.sleep(1)
    Fliseblock.camDown(robot, 200)    
    time.sleep(1)
    Fliseblock.camLeft(robot, 200)
    time.sleep(1)
    Fliseblock.camRight(robot, 200)
    time.sleep(1)