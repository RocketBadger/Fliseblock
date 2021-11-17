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
#  will be deserialized later in the opencv code
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
                #cv2.imshow('abc', )
                jpg_as_text = base64.b64encode(buffer)

                footage_socket.send(jpg_as_text)
            except KeyboardInterrupt:
                break

currentFrame = 0

while(True):
    # Create a camera by just giving the ttyACM depending on your connection value
    # Change the following line depending on your connection
    cap = Camera(device='/dev/ttyACM0')
    # Capture frame-by-frame
    # im1 = cap.read_image()
    # print(im1)
    
    camThread = threading.Thread(target=cap.read_image())
    camThread.start()
    camThread.join()
    time.sleep(2)
    print("Camera thread is alive: " + str(camThread.is_alive()))
    
    # # Our operations on the frame come here
    # gray = cv2.cvtColor(im1, cv2.COLOR_BGR2GRAY)

    # # Saves image of the current frame in jpg file
    # # name = 'frame' + str(currentFrame) + '.jpg'
    # # cv2.imwrite(name, frame)

    # # Display the resulting frame
    # cv2.imshow('im1',im1)
    # # cv2.imshow('im1',gray)

    # if cv2.waitKey(1) & 0xFF == ord('q'):
    #     break

    # # To stop duplicate images
    # currentFrame += 1
