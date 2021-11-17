import serial
import base64
import cv2
import zmq
import threading

ser = 0

def sensorOpen():
    global ser
    ser = serial.Serial('/dev/ttyACM0',9600)  # open serial port
    print(ser.name)

def sensorClose():
    global ser
    ser.close()


def sensorGetImage():
    global ser
    image = 0
    print("waiting...")
    try:
        # ser.flushInput()
        # print("flushed input")
        image = ser.readline()
        print("got image")
        print(image)
    except:
        print("getImage exception")
        pass
    return image        

def send_camera():
    context = zmq.Context()
    footage_socket = context.socket(zmq.PUB)
    footage_socket.connect('tcp://192.168.0.212:5555')
    camera = cv2.VideoCapture(0)  # init the camera
    while True:
        try:
            grabbed, frame = camera.read()  # grab the current frame
            # print(grabbed, frame)
            frame = cv2.resize(frame, (640, 480))  # resize the frame
            encoded, buffer = cv2.imencode('.jpg', frame)
            #cv2.imshow('abc', )
            jpg_as_text = base64.b64encode(buffer)
            footage_socket.send(jpg_as_text)
        except KeyboardInterrupt:
            camera.release()
            cv2.destroyAllWindows()
            break

camThread = threading.Thread(target=send_camera, daemon=True)
camThread.start()
camThread.join()

# while True:
#     sensorOpen()
#     sensorGetImage()
    # print(image)
    # sensorClose()

# def sensorGetTemp():
#     global ser

#     temp=0
#     print("waiting...")
#     try:
#         ser.flushInput()
#         print("flushed input")
#         temp = float(ser.readline())
#         print("got temp")
#     except:
#         print("getTemp exception")
#         pass
#     return temp