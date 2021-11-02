from Raspblock import Raspblock # Note that this imports from dist-packages

robbie = Raspblock()

count = 0

while True: 
    if count > 3000:
        count = 0
    Raspblock.Servo_control(robbie, count, 0)
    count = count + 1
    print(count)
    