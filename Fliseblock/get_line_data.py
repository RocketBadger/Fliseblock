import serial, threading
import numpy as np
# Camera object to create the snaps/frames/images that
#  will be deserialized later
class Camera:
    def __init__(self, device='/dev/ttyACM0'):
        """Reads images from OpenMV Cam
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
        # Important: reset buffers for reliabile restarts of OpenMV Cam
        self.port.reset_input_buffer()
        self.port.reset_output_buffer()

    def read_lines(self):
        """Read image from OpenMV Cam
        Returns:
            image (ndarray): Image
        Raises:
            serial.SerialException
        """
        while True:
            try:
                # Sending 'snap' command causes camera to take snapshot
                self.port.write(str.encode('snap'))
                self.port.flush()
                data = self.port.read(1024) # getting data from camera
                lines = np.array(str(data).split("}")) # splitting data into lines
                for line in lines:
                    print(line)
                    # should be able to perform other operations here
            except KeyboardInterrupt:
                break
            
    def get_lines():
        cap = Camera(device='/dev/ttyACM0')
        camThread = threading.Thread(target=cap.read_lines, daemon=True)
        camThread.start()
