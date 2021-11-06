from Raspblock import Raspblock

# robbie = Raspblock()

class Fliseblock():
    def __init__(self):
        self.robot = Raspblock()
        
        global leftrightpulse
        leftrightpulse = 1500
        global updownpulse
        updownpulse = 1500
    
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
