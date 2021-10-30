# -*- coding:utf-8 -*
import RPi.GPIO as GPIO
import time
import string
import serial

#设置GPIO口为BCM编码方式
GPIO.setmode(GPIO.BCM)

class Raspblock():
    def __init__(self):
        self.ser = serial.Serial("/dev/ttyAMA0", 115200, timeout = 0.001)
        print ("serial Open!")
    
    def __del__(self):
        self.ser.close()
        print ("serial Close!")

    def PID_Mode_control(self, Mode, Speed_KP, Speed_KI, Location_KP, Location_KI, Location_KD, Yaw_holdKP, Yaw_holdKI, Yaw_holdKD):
        Function = 1
        Length = 9
        if(Mode == 0 or Mode == 1):
            Run_Mode = Mode
        Velocity_KP = Speed_KP
        Velocity_KI = Speed_KI
        Position_KP = Location_KP
        Position_KI = Location_KI
        Position_KD = Location_KD
        Yaw_hold_KP = Yaw_holdKP
        Yaw_hold_KI = Yaw_holdKI
        Yaw_hold_KD = Yaw_holdKD
        
        Checknum = (Function + Length + Run_Mode + Velocity_KP + Velocity_KI + Position_KP + Position_KI + Position_KD + Yaw_holdKP + Yaw_holdKI + Yaw_holdKD) & 0xff
        PID_CMD = [0xFF, 0xFE, Function, Length, Run_Mode, Velocity_KP, Velocity_KI, Position_KP, Position_KI, Position_KD, Yaw_holdKP, Yaw_holdKI, Yaw_holdKD, Checknum]
#         print(bytes(PID_CMD))
        self.ser.write(bytes(PID_CMD))
        
    def Servo_control(self, angle_1, angle_2):
        Function = 2
        Length = 4
        if angle_1 < 500:
            angle_1 = 500
        elif angle_1 > 2500:
            angle_1 = 2500
        
        if angle_2 < 500:
            angle_2 = 500
        elif angle_2 > 1950:
            angl_2 = 1950
        
        ServoA_H = (angle_1 >> 8) & 0x00ff # 50(0x32) - 250(0xFA)
        ServoA_L = angle_1 & 0x00ff
        ServoB_H = (angle_2 >> 8) & 0x00ff  # 现在使用的电机因为线太短暂时限制到110
        ServoB_L = angle_2 & 0x00ff
        
        Checknum = (Function + Length + ServoA_H + ServoA_L + ServoB_H + ServoB_L) & 0xff
        Servo_CMD = [0xFF, 0xFE, Function, Length, ServoA_H, ServoA_L, ServoB_H, ServoB_L, Checknum]
#         print(bytes(Servo_CMD))
        self.ser.write(bytes(Servo_CMD))
        
    def Speed_axis_control(self, Speed_axis_X, Speed_axis_Y, Speed_axis_Z):
        Function = 3
        Length = 8
        Speed_axis_Mode = 0x01
        Speed_axis_XH = (abs(Speed_axis_X) >> 8) & 0xff
        Speed_axis_XL = abs(Speed_axis_X) & 0xff
        Speed_axis_YH = (abs(Speed_axis_Y) >> 8) & 0xff
        Speed_axis_YL = abs(Speed_axis_Y) & 0xff
        Speed_axis_ZH = (abs(Speed_axis_Z) >> 8) & 0xff
        Speed_axis_ZL = abs(Speed_axis_Z) & 0xff

        if(Speed_axis_X < 0):
            axis_X_direction = 1
        else:
            axis_X_direction = 0
        if(Speed_axis_Y < 0):
            axis_Y_direction = 1
        else:
            axis_Y_direction = 0
        if(Speed_axis_Z < 0):
            axis_Z_direction = 0
        else:
            axis_Z_direction = 1
            
        Speed_axis_X_direction = axis_X_direction << 2 # 0为正向移动,0x04为负向移动
        Speed_axis_Y_direction = axis_Y_direction << 1 # 0为正向移动,0x02为负向移动
        Speed_axis_Z_direction = axis_Z_direction      # 0为正向转动,0x01为负向转动

        Speed_axis_direction = Speed_axis_X_direction | Speed_axis_Y_direction | Speed_axis_Z_direction
        Checknum = (Function + Length + Speed_axis_Mode + Speed_axis_XH + Speed_axis_XL + Speed_axis_YH + Speed_axis_YL + Speed_axis_ZH + Speed_axis_ZL + Speed_axis_direction) & 0xff
        Speed_Motion_CMD1 = [0xFF, 0xFE, Function, Length, Speed_axis_Mode, Speed_axis_XH, Speed_axis_XL, Speed_axis_YH, Speed_axis_YL, Speed_axis_ZH, Speed_axis_ZL, Speed_axis_direction, Checknum]
#         print(bytes(Speed_Motion_CMD1))
        self.ser.write(bytes(Speed_Motion_CMD1))
        
        
    def Speed_axis_Yawhold_control(self, Speed_axis_X, Speed_axis_Y):
        Function = 3
        Length = 8
        Speed_axis_Mode = 0x03
        Speed_axis_XH = (abs(Speed_axis_X) >> 8) & 0xff
        Speed_axis_XL = abs(Speed_axis_X) & 0xff
        Speed_axis_YH = (abs(Speed_axis_Y) >> 8) & 0xff
        Speed_axis_YL = abs(Speed_axis_Y) & 0xff
        
        if(Speed_axis_X < 0):
            axis_X_direction = 1
        else:
            axis_X_direction = 0
        if(Speed_axis_Y < 0):
            axis_Y_direction = 1
        else:
            axis_Y_direction = 0
        
        Speed_axis_X_direction = axis_X_direction << 2 # 0为正向移动,0x04为负向移动
        Speed_axis_Y_direction = axis_Y_direction << 1 # 0为正向移动,0x02为负向移动
            
        Speed_axis_direction = Speed_axis_X_direction | Speed_axis_Y_direction
        Checknum = (Function + Length + Speed_axis_Mode + Speed_axis_XH + Speed_axis_XL + Speed_axis_YH + Speed_axis_YL + Speed_axis_direction) & 0xff
        Speed_Motion_CMD1 = [0xFF, 0xFE, Function, Length, Speed_axis_Mode, Speed_axis_XH, Speed_axis_XL, Speed_axis_YH, Speed_axis_YL, 0, 0, Speed_axis_direction, Checknum]
#         print(bytes(Speed_Motion_CMD1))
        self.ser.write(bytes(Speed_Motion_CMD1))
        
    def Speed_Wheel_control(self, Speed_WheelA, Speed_WheelB, Speed_WheelC, Speed_WheelD):
        Function = 3
        Length = 8
        Speed_Wheel_Mode = 0x02
        Speed_Wheel_A = abs(Speed_WheelA) & 0xff
        Speed_Wheel_B = abs(Speed_WheelB) & 0xff
        Speed_Wheel_C = abs(Speed_WheelC) & 0xff
        Speed_Wheel_D = abs(Speed_WheelD) & 0xff
        Speed_Wheel_Reserved1 = 0x00
        Speed_Wheel_Reserved2 = 0x00

        if(Speed_WheelA < 0):
            Wheel_A_direction = 1
        else:
            Wheel_A_direction = 0
        if(Speed_WheelB < 0):
            Wheel_B_direction = 1
        else:
            Wheel_B_direction = 0
        if(Speed_WheelC < 0):
            Wheel_C_direction = 1
        else:
            Wheel_C_direction = 0
        if(Speed_WheelD < 0):
            Wheel_D_direction = 1
        else:
            Wheel_D_direction = 0
        
        Speed_Wheel_A_direction = Wheel_A_direction << 0 # 0为正转,0x01为反转
        Speed_Wheel_B_direction = Wheel_B_direction << 1 # 0为正转,0x02为反转
        Speed_Wheel_C_direction = Wheel_C_direction << 2 # 0为正转,0x04为反转
        Speed_Wheel_D_direction = Wheel_D_direction << 3 # 0为正转,0x04为反转

        Speed_wheel_direction = Speed_Wheel_A_direction | Speed_Wheel_B_direction | Speed_Wheel_C_direction | Speed_Wheel_D_direction
        Checknum = (Function + Length + Speed_Wheel_Mode + Speed_Wheel_A + Speed_Wheel_B + Speed_Wheel_C + Speed_Wheel_D + Speed_wheel_direction) & 0xff
        Speed_Motion_CMD2 = [0xFF, 0xFE, Function, Length, Speed_Wheel_Mode, Speed_Wheel_A, Speed_Wheel_B, Speed_Wheel_C, Speed_Wheel_D, Speed_Wheel_Reserved1, Speed_Wheel_Reserved2, Speed_wheel_direction, Checknum]
#         print(bytes(Speed_Motion_CMD2))
        self.ser.write(bytes(Speed_Motion_CMD2))
        
    def Position_disp_control(self, Position_disp_X, Position_disp_Y, Position_disp_Z):
        Function = 3
        Length = 8
        Position_disp_Mode = 0x04
        Position_disp_XH = (abs(Position_disp_X) >> 8) & 0x00ff
        Position_disp_XL = abs(Position_disp_X) & 0x00ff
        Position_disp_YH = (abs(Position_disp_Y) >> 8) & 0x00ff
        Position_disp_YL = abs(Position_disp_Y) & 0x00ff
        Position_disp_ZH = (abs(Position_disp_Z) >> 8) & 0x00ff
        Position_disp_ZL = abs(Position_disp_Z) & 0x00ff

        if(Position_disp_X < 0):
            Position_disp_X_direction = 0
        else:
            Position_disp_X_direction = 1
        if(Position_disp_Y < 0):
            Position_disp_Y_direction = 0
        else:
            Position_disp_Y_direction = 1
        if(Position_disp_Z < 0):
            Position_disp_Z_direction = 0
        else:
            Position_disp_Z_direction = 1
        
        Position_disp_X_direction = Position_disp_X_direction << 0 # 0为正向移动,0x01为负向移动
        Position_disp_Y_direction = Position_disp_Y_direction << 1 # 0为正向移动,0x02为负向移动
        Position_disp_Z_direction = Position_disp_Z_direction << 2 # 0为正向转动,0x04为负向转动

        Position_disp_direction = Position_disp_X_direction | Position_disp_Y_direction | Position_disp_Z_direction
        Checknum = (Function + Length + Position_disp_Mode + Position_disp_XH + Position_disp_XL + Position_disp_YH + Position_disp_YL + Position_disp_ZH + Position_disp_ZL + Position_disp_direction) & 0xff
        Position_Motion_CMD = [0xFF, 0xFE, Function, Length, Position_disp_Mode, Position_disp_XH, Position_disp_XL, Position_disp_YH, Position_disp_YL, Position_disp_ZH, Position_disp_ZL, Position_disp_direction, Checknum]
#         print(bytes(Position_Motion_CMD))
        self.ser.write(bytes(Position_Motion_CMD))
    
    def Buzzer_control(self, switch_state):
        Function = 4
        Length = 1
        if switch_state == 0 or switch_state == 1:
            Checknum = (Function + Length + switch_state) & 0xff
            Buzzer_CMD = [0xFF, 0xFE, Function, Length, switch_state, Checknum]
    #         print(bytes(Servo_CMD))
            self.ser.write(bytes(Buzzer_CMD))
    