from Raspblock import Raspblock # Note that this imports from dist-packages

robbie = Raspblock()

count = 0

while True: 
    if count > 1500:
        count = 0
    Raspblock.Servo_control(robbie, 0, count)
    count = count + 1
