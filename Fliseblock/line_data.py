import serial, threading, json, math
import numpy as np

class Camera:
    def __init__(self, device='/dev/ttyACM0'):
        """Reads lines from OpenMV Cam
        Args:
            device (str): Serial device
        Raises:
            serial.SerialException
        """
        self.port = serial.Serial(device, baudrate=115200,
                                  bytesize=serial.EIGHTBITS,
                                  parity=serial.PARITY_NONE,
                                  xonxoff=False, rtscts=False,
                                  stopbits=serial.STOPBITS_ONE,
                                  timeout=None, dsrdtr=True)
        # Reset buffers for reliable restarts of OpenMV Cam
        self.port.reset_input_buffer()
        self.port.reset_output_buffer()
    
    def line_to_theta_and_rho(self, line):
        if line.rho < 0: # quadrant 3/4
            if line.theta < 90: # quadrant 3 (unused)
                return (math.sin(math.radians(line.theta)),
                    math.cos(math.radians(line.theta + 180)) * -line.rho)
            else: # quadrant 4
                return (math.sin(math.radians(line.theta - 180)),
                    math.cos(math.radians(line.theta + 180)) * -line.rho)
        else: # quadrant 1/2
            if line.theta < 90: # quadrant 1
                if line.theta < 45:
                    return (math.sin(math.radians(180 - line.theta)),
                        math.cos(math.radians(line.theta)) * line.rho)
                else:
                    return (math.sin(math.radians(line.theta - 180)),
                        math.cos(math.radians(line.theta)) * line.rho)
            else: # quadrant 2
                return (math.sin(math.radians(180 - line.theta)),
                    math.cos(math.radians(line.theta)) * line.rho)
    

    def read_lines(self):
        """Read line data gained by linear regression from OpenMV Cam
            Returns:
            A sequence of variables representing different characteristics of a line
                Example: {'x1': 67, 'y1': 0, 'x2': 12, 'y2': 59, 'length': 81, 'magnitude': 16, 'theta': 43, 'rho': 49}
            Where 
                x and y are the coordinates of the line. 
                    length is the length of the line. 
                        magnitude is the strength of the line detection. A simple threshold on it is enough to accept or reject the line.
                            theta and rho is the angle of the line, using polar math.
        Raises:
            KeyboardInterrupt
        """
        while True:
            try:
                # Sending 'snap' command causes camera to take snapshot
                self.port.write(str.encode('snap'))
                self.port.flush()
                waiting = self.port.inWaiting()
                # print(waiting)
                data = self.port.read(waiting) # getting data from camera
                # print(data)
                # lines = np.array(str(data).split("}")) # splitting data into lines
                
                # for line in lines:
                # if "x1" and "rho" in data: # if line is whole
                # if waiting > 80:
                if str(data).count('x1') == 1: # ignore doubled lines
                    line = json.loads(data) # convert to dict
                    Linedata = line_data(line['x1'], line['y1'], line['x2'], line['y2'], line['length'], line['magnitude'], line['theta'], line['rho']) # create line data object. Necessary? could dict be used all over instead?
                    # print("Line data == " + str(Linedata.__dict__))
                    print(Linedata.x1)
                    if ((Linedata.x1 - Linedata.x2) > -10 and (Linedata.x1 - Linedata.x2) < 10):
                        print("Line is vertical")
                    if ((Linedata.y1 - Linedata.y2) > -10 and (Linedata.y1 - Linedata.y2) < 10):
                        print("Line is horizontal")
                    # # print("line_to_theta_and_rho says: " + str(line_to_theta_and_rho(Linedata)))
                    # print("line_to_theta_and_rho says: " + str(self.line_to_theta_and_rho(Linedata)))
            except KeyboardInterrupt:
                print(data)
                break
            
    def get_lines():
        cap = Camera(device='/dev/ttyACM0')
        camThread = threading.Thread(target=cap.read_lines, daemon=True)
        camThread.start()

class line_data():
    """An object representing a line.
    """
    def __init__(self, x1, y1, x2, y2, length, magnitude, theta, rho):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.length = length
        self.magnitude = magnitude
        self.theta = theta
        self.rho = rho
      