from Fliseblock import Fliseblock
import time
from Tests import *

robbie = Fliseblock()

camServosTest(robbie)

Fliseblock.wheel_control_forwards(robbie, 500)
Fliseblock.wheel_control_backwards(robbie, 500)

