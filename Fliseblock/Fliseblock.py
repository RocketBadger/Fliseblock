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
    Initialize camera position, and set the servo to the middle position
    """
    def camInit(self):
        global leftrightpulse, updownpulse
        leftrightpulse = 1500
        updownpulse = 600
        self.robot.Servo_control(leftrightpulse, updownpulse)
        print("Camera initialized")
    
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
        print("Camera up")
        
    def camDown(self, num):
        global updownpulse
        updownpulse += num
        if updownpulse < 500:
            updownpulse = 500
        self.robot.Servo_control(leftrightpulse, updownpulse)
        print("Camera down")
        
    def camLeft(self, num):
        global leftrightpulse
        leftrightpulse += num
        if leftrightpulse > 2500:
            leftrightpulse = 2500
        self.robot.Servo_control(leftrightpulse, updownpulse)
        print("Camera left")
    
    def camRight(self, num):
        global leftrightpulse
        leftrightpulse -= num
        if leftrightpulse < 500:
            leftrightpulse = 500
        self.robot.Servo_control(leftrightpulse, updownpulse)
        print("Camera right")
        
    """
    Movement functions 
    """
    #TODO: Add a function to move the robot in a straight line
    # inspiration in Raspblock.py, and PID.py
    def wheel_control_forwards(self, duration):
        print("Forwards")
        # if duration == 0:
        #     while True:
        #         self.robot.Speed_Wheel_control(8, 8, 8, 8)
        for i in range (1, duration):
            self.robot.Speed_Wheel_control(8, 8, 8, 8)
            print(i)

    def wheel_control_backwards(self, duration):
        print("Backwards")
        for i in range (1, duration):
            self.robot.Speed_Wheel_control(-8, -8, -8, -8)
            print(i)

    #Spin left and spin right both a little iffy
    def wheel_control_spin_left(self, duration):
        print("Left")
        for i in range (1, duration):
            self.robot.Speed_Wheel_control(8, -8, -8, 8)
            print(i)
            
    def wheel_control_spin_right(self, duration):
        print("Right")
        for i in range (1, duration):
            self.robot.Speed_Wheel_control(-8, 8, 8, -8)
            print(i)
    
    def wheel_control_stop(self):
        print("Stop")
        self.robot.Speed_Wheel_control(0, 0, 0, 0)