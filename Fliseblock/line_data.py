import serial, threading, json
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

    def read_lines(self):
        """Read line data gained by linear regression from OpenMV Cam
        Returns:
            A sequence of variables representing different characteristics of a line
                Example: {"x1":211, "y1":0, "x2":134, "y2":239, "length":251, "magnitude":51, "theta":18, "rho":201}
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
                data = self.port.read(1024) # getting data from camera
                lines = np.array(str(data).split("}")) # splitting data into lines
                for line in lines:
                    if line[0] == '{' and "rho" in line: # if line is whole
                        line = line + "}" # add closing bracket removed by split
                        print(line)
                        line = json.loads(line) # convert to dict
                        print(line)
                        # data = line.split()
                        
                        # i = 0
                        # for var in data:
                        #     print(var)
                        #     for char in var:
                        #         num = ""
                        #         if char.isdigit():
                        #             num = num + char
                        #         line_data()[i] = int(num)
                        #     print(line_data()[i])
                        #     i = i + 1

            except KeyboardInterrupt:
                break
            
    def get_lines():
        cap = Camera(device='/dev/ttyACM0')
        camThread = threading.Thread(target=cap.read_lines)
        camThread.start()

    def line_to_theta_and_rho(line):
        if line.rho() < 0: # quadrant 3/4
            if line.theta() < 90: # quadrant 3 (unused)
                return (math.sin(math.radians(line.theta())),
                    math.cos(math.radians(line.theta() + 180)) * -line.rho())
            else: # quadrant 4
                return (math.sin(math.radians(line.theta() - 180)),
                    math.cos(math.radians(line.theta() + 180)) * -line.rho())
        else: # quadrant 1/2
            if line.theta() < 90: # quadrant 1
                if line.theta() < 45:
                    return (math.sin(math.radians(180 - line.theta())),
                        math.cos(math.radians(line.theta())) * line.rho())
                else:
                    return (math.sin(math.radians(line.theta() - 180)),
                        math.cos(math.radians(line.theta())) * line.rho())
            else: # quadrant 2
                return (math.sin(math.radians(180 - line.theta())),
                    math.cos(math.radians(line.theta())) * line.rho())

    def line_to_theta_and_rho_error(line, img):
        t, r = line_to_theta_and_rho(line)
        return (t, r - (img.width() // 2))
    
class line_data():
    def __init__(self, x1, y1, x2, y2, length, magnitude, theta, rho):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.length = length
        self.magnitude = magnitude
        self.theta = theta
        self.rho = rho
    
        
        