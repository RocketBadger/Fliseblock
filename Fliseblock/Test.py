from Fliseblock import Fliseblock
import time

robbie = Fliseblock()

Fliseblock.camInit(robbie)
print("Camera initialized")
time.sleep(2)
Fliseblock.camUp(robbie, 50)
print("Camera up")
time.sleep(2)
Fliseblock.camDown(robbie, 50)    
print("Camera down")