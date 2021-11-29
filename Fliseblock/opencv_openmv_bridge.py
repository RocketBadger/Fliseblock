import numpy as np
import io
import struct
import serial
from PIL import Image as PILImage
import cv2
import base64
import zmq
import threading
import time

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

    def read_image(self):
        """Read image from OpenMV Cam
        Returns:
            image (ndarray): Image
        Raises:
            serial.SerialException
        """
        context = zmq.Context()
        footage_socket = context.socket(zmq.PUB)
        footage_socket.connect('tcp://192.168.0.39:5555')
        
        while True:
            try:
                # Sending 'snap' command causes camera to take snapshot
                self.port.write(str.encode('snap'))
                self.port.flush()
                # Read 'size' bytes from serial port
                size = struct.unpack('<L', self.port.read(4))[0]
                image_data = self.port.read(size)
                image = np.array(PILImage.open(io.BytesIO(image_data)))
                print(image)
                frame = cv2.resize(image, (640, 480))  # resize the frame
                encoded, buffer = cv2.imencode('.jpg', frame)
                jpg_as_text = base64.b64encode(buffer)
                footage_socket.send(jpg_as_text)
            except KeyboardInterrupt:
                break
            
    def send_image():
        cap = Camera(device='/dev/ttyACM0')
        camThread = threading.Thread(target=cap.read_image)
        camThread.start()
        # camThread.join()
