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
        ser.flushInput()
        print("flushed input")
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

while True:
    sensorOpen()
    image = sensorGetImage()
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