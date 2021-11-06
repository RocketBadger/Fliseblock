from Raspblock import Raspblock

# robbie = Raspblock()

class Fliseblock():
    def __init__(self):
        self.robot = Raspblock()
        
        global leftrightpulse
        leftrightpulse = 0
        global updownpulse
        updownpulse = 0
    
    """
    Camera functions
    camUp + camDown control the upper servo
    camLeft + camRight control the lower servo
    50 appears to be the smallest value that the servo can move
    """
    def camUp(self, num):
        global updownpulse
        updownpulse -= num
        if updownpulse > 2500:
            updownpulse = 2500
        self.robot.Servo_control(leftrightpulse, updownpulse)
        
    def camDown(self, num):
        global updownpulse
        updownpulse += num
        if updownpulse < 500:
            updownpulse = 500
        self.robot.Servo_control(leftrightpulse, updownpulse)
        
    def camLeft(self, num):
        global leftrightpulse
        leftrightpulse += num
        if leftrightpulse > 2500:
            leftrightpulse = 2500
        self.robot.Servo_control(leftrightpulse, updownpulse)
    
    def camRight(self, num):
        global leftrightpulse
        leftrightpulse -= num
        if leftrightpulse < 500:
            leftrightpulse = 500
        self.robot.Servo_control(leftrightpulse, updownpulse)
        
    """
    Initialize camera position, and set the servo to the middle position
    """
    def camInit(self):
        global leftrightpulse, updownpulse
        leftrightpulse = 1500
        updownpulse = 600
        self.robot.Servo_control(leftrightpulse, updownpulse)
        
    """
    Movement functions 
    """
    #TODO: Add a function to move the robot in a straight line
    # inspiration in Raspblock.py, and PID.py
