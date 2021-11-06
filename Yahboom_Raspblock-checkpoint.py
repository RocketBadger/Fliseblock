#!/usr/bin/env Python
# coding=utf-8
'''
@Copyright (C): 2010-2022, Shenzhen Yahboom Tech
@Author: Malloy.Yuan
@Date: 2019-08-02 12:03:42
@LastEditors  : Liusen
@LastEditTime : 2020-03-23 16:15:03
'''


from flask import Flask, render_template, Response
from importlib import import_module
import os, serial, socket, base64, hashlib, sys, struct, threading, hashlib, re, time, cv2, PID, pygame
import numpy as np
from Raspblock import Raspblock
from aip import AipSpeech
import pyzbar.pyzbar as pyzbar
from PIL import Image, ImageDraw, ImageFont
import tensorflow as tf
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_utils


#Gesture recognition
import demjson
from aip import AipBodyAnalysis

# For specific hand signals, please see the official offer: https://ai.baidu.com/ai-doc/BODY/4k3cpywrv
hand = {'One':'one', 
 'Five':'five',  'Fist':'fist',  'Ok':'OK',  'Prayer':'pray', 
 'Congratulation':'congratulation',  'Honour':'honour',  'Heart_single':'heart_single', 
 'Thumb_up':'thumb_up',  'Thumb_down':'thumb_down',  'ILY':'i_love_you', 
 'Palm_up':'palm_up',  'Heart_1':'Heart_one',  'Heart_2':'Heart_tow', 
 'Heart_3':'Heart_three',  'Two':'two',  'Three':'three', 
 'Four':'four',  'Six':'six',  'Seven':'seven',  'Eight':'eight', 
 'Nine':'nine',  'Rock':'Rock',  'Face':'face'}

# The following key should be replaced with your own 
""" Body Analysis APPID AK SK """
APP_ID_Body = '18550528'
API_KEY_Body = 'K6PWqtiUTKYK1fYaz13O8E3i'
SECRET_KEY_Body = 'IDBUII1j6srF1XVNDX32I2WpuwBWczzK'
client_body = AipBodyAnalysis(APP_ID_Body, API_KEY_Body, SECRET_KEY_Body)

""" Your APPID AK SK """
APP_ID = '17852430'
API_KEY = 'eGeO4iQGAjHCrzBTYd1uvTtf'
SECRET_KEY = 'Cn1EVsUngZDbRLv4OxAFrDHSo8PsvFVP'

client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)

#Log file module
import logging
from logging import handlers

class Logger(object):
    level_relations = {
        'debug':logging.DEBUG,
        'info':logging.INFO,
        'warning':logging.WARNING,
        'error':logging.ERROR,
        'crit':logging.CRITICAL
    }#Log level relationship mapping

    def __init__(self,filename,level='info',when='D',backCount=3,fmt='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'):
        self.logger = logging.getLogger(filename)
        format_str = logging.Formatter(fmt)# Setting the log format
        self.logger.setLevel(self.level_relations.get(level))# Setting the log level
        sh = logging.StreamHandler()# Output to the screen
        sh.setFormatter(format_str) # Set the format displayed on the screen
        th = handlers.TimedRotatingFileHandler(filename=filename,when=when,backupCount=backCount,encoding='utf-8')# Write to the file # Specify the processor that automatically generates the file at the specified interval
        # Instantiating the TimedRotatingFileHandler
        # interval is the time interval, backupCount is the number of backup files that will be automatically deleted if this number is exceeded, and when is the unit of time for the interval, in the following units.
        # S seconds
        # M minutes
        # H hours, # D days
        # D days.
        # W per week (interval==0 for Mondays)
        # midnight Every day in the early hours of the morning
        th.setFormatter(format_str)# Set the format written in the file
        self.logger.addHandler(sh) # Adding objects to the logger
        self.logger.addHandler(th)

# Interface function mode status machine
#| 1 -> remote_control | 2 -> mecanum_control | 3 -> mode_presentation | 4 -> target_track | 5 -> tag_identification | 6 -> voice_broadcast | 7 -> auto_drive _identification) | 6 -> voice_broadcast | 7 -> auto_drive
global g_mode
g_mode = '0'

# remote_control -- servo_motion_mode_sub-state_machine
# 1-6(up(servo_forward)|down(servo_down)|left(servo_left)|right(servo_right)|stop(0)|center(servo_init))
global g_servormode
g_servormode = '0'

#remote_control -- motion mode sub-state machine
# 0(Free) | 1(Stabilize) 
global g_robot_motion_mode
g_robot_motion_mode = 'Free'  # Stabilize / Free

#remote_control - yaw angle change sub-state machine
# unlock / lock
global g_z_state
g_z_state = 'unlock'  # unlock / lock

# Mode presentation - presentation sub-state machine
# 0 - > Presentation mode selection main screen (0) | 1 - > Round mode | 2 - > Translation mode | 3 - > Stabilize mode | 4 - > Position mode
global g_presentation_mode
g_presentation_mode = '0'

# Mode presentation - presentation sub-state machine
# 0 - > Do not update values | 1 - > Update values
global g_Position_update
g_Position_update = 0

#target_track - tracking mode sub-state machine
# 0 | face_track | color_track | meanshift_track
global g_target_mode
g_target_mode = '0'

# tag_identification -- recognition mode sub-state machine
# 1 -> QR code recognition (qrcode) | 2 -> object detection (object)
global g_tag_select
g_tag_select = 'qrcode'

# tag_identification -- Identify the switch sub-state machine
# 0 -> off (close) | 1 -> on (open)
global g_tag_identify_switch
g_tag_identify_switch = 'close'

# tag_identification -- Identification of the broadcast switch sub-state machine
# 0 -> off (close) | 1 -> on (open)
global g_tag_brodcast_switch
g_tag_brodcast_switch = 'close'

# autodrive interface (auto_drive) -- autodrive switch sub-state machine
# 0 -> off (close) | 1 -> on (open)
global g_auto_drive_switch
g_auto_drive_switch = 'close'

# auto_drive -- auto_drive screen switch sub-state machine
# 0 -> origin_view | 1 -> bird_view | 2 -> lane_view
global g_drive_view_switch
g_drive_view_switch = 0

# Motion process variables
global Speed_axis_X,Speed_axis_Y,Speed_axis_Z
Speed_axis_X = 0
Speed_axis_Y = 0
Speed_axis_Z = 0
global Speed_WheelA,Speed_WheelB,Speed_WheelC,Speed_WheelD
Speed_WheelA = 0
Speed_WheelB = 0
Speed_WheelC = 0
Speed_WheelD = 0
global Position_disp_X,Position_disp_Y,Position_disp_Z
Position_disp_X = 0
Position_disp_Y = 0
Position_disp_Z = 0
global Max_speed_XY, Max_speed_Z
Max_speed_XY = 12
Max_speed_Z = 12

#move tracking parameters set variables
global meanshift_X, meanshift_Y, meanshift_width, meanshift_high, meanshift_update_flag
meanshift_X = 0
meanshift_Y = 0
meanshift_width = 40
meanshift_high = 40
meanshift_update_flag = 0

global g_init
g_init = False
global leftrightpulse
leftrightpulse = 1500
global updownpulse
updownpulse = 1500
global color_lower
color_lower=np.array([156,43,46])
global color_upper
color_upper = np.array([180, 255, 255])
global target_valuex
target_valuex = 1500
global target_valuey
target_valuey = 1500

'''

global config_ip,config_left_speed,config_right_speed
config_file = open("/home/pi/yahboom-raspblock/config.txt", "r")
lines = config_file.readlines()  #Read all the contents of a file by line
pattern = re.compile('"(.*)"')
config_ip = pattern.findall(lines[0])
print('IP address: %s'%config_ip[0])
config_file.close()

'''


robot = Raspblock()

HANDSHAKE_STRING = "HTTP/1.1 101 Switching Protocols\r\n" \
      "Upgrade:websocket\r\n" \
      "Connection: Upgrade\r\n" \
      "Sec-WebSocket-Accept: {1}\r\n" \
      "WebSocket-Location: ws://{2}/chat\r\n" \
      "WebSocket-Protocol:chat\r\n\r\n"

app = Flask(__name__)
  
@app.route('/')
def index(): 
  return render_template('index.html')

@app.route('/video_feed')
def video_feed():
  return Response(mode_handle(),
          mimetype='multipart/x-mixed-replace; boundary=frame')
  
@app.route('/init')
def init():
    # websocket thread
    # url='http://'+IPAddress+':'+str(VideoPort)+'/init'
    
    if g_init == False:
        tid=threading.Thread(target=start_tcp_server, args=(6000,))
        tid.setDaemon(True)
        tid.start()
    print('init websocket!!!!!!!!!')
    return render_template('init.html')

'''The following sections are for the rudder controls'''
def camUpFunction(num):
    global updownpulse
    updownpulse-=num
    if updownpulse>2500:
        updownpulse=2500
    robot.Servo_control(leftrightpulse, updownpulse)

def camDownFunction(num):
    global updownpulse
    updownpulse+=num
    if updownpulse<500:
        updownpulse=500
    robot.Servo_control(leftrightpulse, updownpulse)

def camLeftFunction(num):
    global leftrightpulse
    leftrightpulse+=num
    if leftrightpulse>2500:
        leftrightpulse=2500
    robot.Servo_control(leftrightpulse, updownpulse)

def camRightFunction(num):
    global leftrightpulse
    leftrightpulse-=num
    if leftrightpulse<500:
        leftrightpulse=500
    robot.Servo_control(leftrightpulse, updownpulse)

def camservoInitFunction():
    global leftrightpulse, updownpulse
    leftrightpulse = 1500
    updownpulse = 1500
    robot.Servo_control(leftrightpulse, updownpulse)

#  Define the conversion function to display Chinese
def cv2ImgAddText(img, text, left, top, textColor=(0, 255, 0), textSize=20):
    if (isinstance(img, np.ndarray)):  #  Determining if an OpenCV image type
        img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    # Create an object that can draw on a given image
    draw = ImageDraw.Draw(img)
    # Formatting of fonts
    fontStyle = ImageFont.truetype(
        "/home/pi/yahboom-raspblock/simhei.ttf", textSize, encoding="utf-8")
    # Drawing text
    draw.text((left, top), text, textColor, font=fontStyle)
    # Convert back to OpenCV format
    return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)

#Wrapping websocket sending functions
def send_msg(conn, msg_bytes):
    import struct
    token = b"\x81"
    length = len(msg_bytes)
    if length < 126:
        token += struct.pack("B", length)
    elif length <= 0xFFFF:
        token += struct.pack("!BH", 126, length)
    else:
        token += struct.pack("!BQ", 127, length)
    msg = token + msg_bytes
    conn.send(msg)
    return True

#Get IP current address
def getip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('www.baidu.com', 0))
        ip = s.getsockname()[0]
    except:
        ip = "x.x.x.x"
    finally:
        s.close()
    return ip

#websocket communication establishment
def start_tcp_server(port):
    global g_init, g_socket
    g_init = True

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ip = getip()
    while(ip == "x.x.x.x"):
        time.sleep(5)
    
    sock.bind((ip, port))
    sock.listen(5)
    while True:
        conn, address = sock.accept()
        g_socket = conn
        request = conn.recv(2048)
        print(request.decode())
        # 获取Sec-WebSocket-Key
        ret = re.search(r"Sec-WebSocket-Key: (.*==)", str(request.decode()))
        if ret:
            key = ret.group(1)
        else:
            return
        Sec_WebSocket_Key = key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
        # Sec-WebSocket-Key is first encrypted with sha1, converted to binary and then encrypted with base64
        response_key = base64.b64encode(hashlib.sha1(bytes(Sec_WebSocket_Key, encoding="utf8")).digest())
        response_key_str = str(response_key)
        response_key_str = response_key_str[2:30]
        # Constructing websocket return data
        response = HANDSHAKE_STRING.replace("{1}", response_key_str).replace("{2}", ip + ":" + str(port))
        conn.send(response.encode())
        #Mobile phones are connected
        pygame.mixer.init()
        pygame.mixer.music.load('/home/pi/yahboom-raspblock/connect.mp3')
        pygame.mixer.music.play()
        handleTid = threading.Thread(target = message_handle, args = [conn])
        handleTid.setDaemon(True)
        handleTid.start()
    closeTid = threading.Thread(target = waitClose, args = [conn])
    closeTid.setDaemon(True)
    closeTid.start()

#Close socket
def waitClose(sock):
    time.sleep(10)
    sock.close()

#Unpacking data
def message_handle(client):
    lastCmd=''
    # handleMode = threading.Thread(target = mode_handle, args = [client])
    # handleMode.setDaemon(True)
    # handleMode.start()
    while True:
        try:
            info = client.recv(8096)
        except Exception as e:
            info = None
        if not info:
            print('break thread')
            break
        payload_len = info[1] & 127
        #print(info)
        print(payload_len)
        if payload_len == 126:
            extend_payload_len = info[2:4]
            mask = info[4:8]
            decoded = info[8:]
        elif payload_len == 127:
            extend_payload_len = info[2:10]
            mask = info[10:14]
            decoded = info[14:]
        else:
            extend_payload_len = None
            mask = info[2:6]
            #decoded = info[6:]
            decoded = info[6:payload_len+6]
 
        bytes_list = bytearray()
        
        for i in range(len(decoded)):
            chunk = decoded[i] ^ mask[i % 4]
            bytes_list.append(chunk)
        
        
        try:
            #body = bytes_list.decode('utf-8')  
            body = str(bytes_list, encoding="utf-8")
        except UnicodeDecodeError:
            body = "$01,X0.00Y0.00#"
            print(bytes_list)
            print('UnicodeDecodeError')
            #continue
            
        gotdata=body 
        print(body)
        

        #Parsing data protocols here
        dispatch(client,body)
            
        # body=body+'just_decode'
        # try:
        #     send_msg(client,body.encode('utf-8'))
        # except UnicodeDecodeError:
        #     print('UnicodeDecodeError')

#Parsing data protocols
def dispatch(sock,cmd):
    global g_servormode, g_mode ,g_target_mode, g_presentation_mode, g_robot_motion_mode, g_z_state, g_tag_select
    global color_lower, color_upper
    global g_tag_identify_switch, g_tag_brodcast_switch
    global Speed_axis_X,Speed_axis_Y,Speed_axis_Z
    global Speed_WheelA, Speed_WheelB, Speed_WheelC, Speed_WheelD
    global Position_disp_X, Position_disp_Y, Position_disp_Z
    global Max_speed_XY, Max_speed_Z
    global meanshift_X, meanshift_Y, meanshift_width, meanshift_high, meanshift_update_flag
    global g_auto_drive_switch, g_drive_view_switch
    global g_Position_update
    global leftrightpulse, updownpulse
        
    cmd_function = cmd[1:3]
    #Omnidirectional wheel movement protocol
    if cmd_function == '01':
        reg = re.compile('^\$01,X(?P<Speed_axis_X>[^ ]*)Y(?P<Speed_axis_Y>[^ ]*)#')
        regMatch = reg.match(cmd)                        
        try:
            if (regMatch != None):
                linebits = regMatch.groupdict()
                Speed_axis_X = int(float(linebits['Speed_axis_X']) * Max_speed_XY)
                Speed_axis_Y = -int(float(linebits['Speed_axis_Y']) * Max_speed_XY)
            else:
                print("cmd-01 expression parse failure!")
        except:
            print('cmd-01 parse failure!')
            pass
    #Left and right steering
    elif cmd_function == '02':
        reg = re.compile('^\$02,(?P<Turn_action>[^ ]*)#')
        regMatch = reg.match(cmd)                        
        try:
            if (regMatch != None):
                linebits = regMatch.groupdict()
                Turn_action = linebits['Turn_action']
                if Turn_action == '1':
                    Speed_axis_Z = -Max_speed_Z
                    g_z_state = 'unlock'
                elif Turn_action == '2':
                    Speed_axis_Z = Max_speed_Z
                    g_z_state = 'unlock'
                elif Turn_action == '3':
                    Speed_axis_Z = 0
                    g_z_state = 'lock'
            else:
                print("cmd-02 expression parse failure!")                
        except:
            print('cmd-02 parse failure!')
            pass
    #Camera motion control
    elif cmd_function == '03':
        reg = re.compile('^\$03,(?P<Servo_action>[^ ]*)#')
        regMatch = reg.match(cmd)                        
        try:
            if (regMatch != None):
                linebits = regMatch.groupdict()
                Servo_action = linebits['Servo_action']
                
                if Servo_action == '1':
                    g_servormode = 'servo_forward'
                elif Servo_action == '2':
                    g_servormode = 'servo_down'
                elif Servo_action == '3':
                    g_servormode = 'servo_left'
                elif Servo_action == '4':
                    g_servormode = 'servo_right'
                elif Servo_action == '5':
                    g_servormode = '0'
                elif Servo_action == '6':
                    g_servormode = 'servo_init'

            else:
                print("cmd-03 expression parse failure!")
        except:
            print('cmd-03 parse failure!')
            pass
    #Colour + Face Tracking
    elif cmd_function == '04':
        reg = re.compile('^\$04,(?P<target_select>[^ ]*)#')
        regMatch = reg.match(cmd)                        
        try:
            if (regMatch != None):
                linebits = regMatch.groupdict()
                target_select = linebits['target_select']
                if target_select == '0':
                    g_target_mode = '0'
                    target_valuex = target_valuey = 1500
                    robot.Servo_control(1500,1500)
                if target_select == '1':
                    g_mode = 'target_track'
                    g_target_mode = 'color_track'
                    color_lower = np.array([0,43,46])
                    color_upper = np.array([10, 255, 255])
                    target_valuex = target_valuey = 1500
                    robot.Servo_control(1500,1500)
                elif target_select == '2':       #绿
                    g_mode = 'target_track'
                    g_target_mode = 'color_track'
                    color_lower = np.array([35,43,46])
                    color_upper = np.array([77, 255, 255])
                    target_valuex = target_valuey = 1500
                    robot.Servo_control(1500,1500)
                elif target_select == '3':       #蓝
                    g_mode = 'target_track'
                    g_target_mode = 'color_track'
                    color_lower = np.array([100,43,46])
                    color_upper = np.array([124, 255, 255])
                    target_valuex = target_valuey = 1500
                    robot.Servo_control(1500,1500)
                elif target_select == '4':       #黄
                    g_mode = 'target_track'
                    g_target_mode = 'color_track'
                    color_lower = np.array([26,43,46])
                    color_upper = np.array([34, 255, 255])
                    target_valuex = target_valuey = 1500
                    robot.Servo_control(1500,1500)
                elif target_select == '5':       #橙
                    g_mode = 'target_track'
                    g_target_mode = 'color_track'
                    color_lower = np.array([11,43,46])
                    color_upper = np.array([25, 255, 255])
                    target_valuex = target_valuey = 1500
                    robot.Servo_control(1500,1500)
                elif target_select == '6':       #无
                    g_target_mode = '0'
                    g_mode = '0'
                    color_lower = np.array([156,43,46])
                    color_upper = np.array([180, 255, 255])
                    target_valuex = target_valuey = 1500
                    robot.Servo_control(1500,1500)
                elif target_select == '7':      #人脸追踪
                    g_mode = 'target_track'
                    g_target_mode = 'face_track'
            else:
                print("cmd-04 expression parse failure!")
        except:
            print('cmd-04 parse failure!')
            pass
    #Audio announcements
    elif cmd_function == '05':
        if cmd[-1] == '#' and cmd[0:4] == '$05,':
            Voice_text = cmd[4:-1]
            if Voice_text != '':
                print('Voice_txt: %s'%Voice_text)
                result = client.synthesis(text = Voice_text, 
                                options={'spd':3,'vol':15,'per':2,})
                #Write the synthesised speech to a file
                if not isinstance(result,dict):
                    with open('/home/pi/yahboom-raspblock/audio.mp3','wb') as f:
                        f.write(result)
                        #We use the pygame that comes with the Raspberry Pi
                        pygame.mixer.init()
                        pygame.mixer.music.load('/home/pi/yahboom-raspblock/audio.mp3')
                        pygame.mixer.music.play()
                else:
                    print(result)
        else:
            print("cmd-05 expression parse failure!")
    #Label recognition
    elif cmd_function == '06':
        reg = re.compile('^\$06,(?P<Recognize_option>[^ ]*)#')
        regMatch = reg.match(cmd)                        
        try:
            if (regMatch != None):
                linebits = regMatch.groupdict()
                Recognize_option = linebits['Recognize_option']
                if Recognize_option[0] == '0':
                    g_tag_identify_switch = 'close'
                elif Recognize_option[0] == '1':
                    g_tag_identify_switch = 'open'
                if Recognize_option[1] == '1':
                    g_tag_select = 'qrcode'
                elif Recognize_option[1] == '2':
                    g_tag_select = 'object'
                elif Recognize_option[1] == '3':
                    g_tag_select = 'gesture'
                
                if Recognize_option[2] == '0':
                    g_tag_brodcast_switch = 'close'
                    identify_tag = ''
                    last_identify_tag = ''
                elif Recognize_option[2] == '1':
                    g_tag_brodcast_switch = 'open'
            else:
                print("cmd-06 expression parse failure!")
        except:
            print('cmd-06 parse failure!')
            pass
    #Motion mode demo mode selection
    elif cmd_function == '07':
        reg = re.compile('^\$07,(?P<Presentation_Mode>[^ ]*)#')
        regMatch = reg.match(cmd)                        
        try:
            if (regMatch != None):
                linebits = regMatch.groupdict()
                Presentation_Mode = linebits['Presentation_Mode']
                if Presentation_Mode == '0':
                    g_presentation_mode = '0'
                    pygame.mixer.init()
                    pygame.mixer.music.load('/home/pi/yahboom-raspblock/ModeClose.mp3')
                    pygame.mixer.music.play()
                elif Presentation_Mode == '1':
                    g_presentation_mode = 'around'
                    pygame.mixer.init()
                    pygame.mixer.music.load('/home/pi/yahboom-raspblock/surrondstart.mp3')
                    pygame.mixer.music.play()
                elif Presentation_Mode == '2':
                    g_presentation_mode = 'translation'
                    pygame.mixer.init()
                    pygame.mixer.music.load('/home/pi/yahboom-raspblock/TranslateStart.mp3')
                    pygame.mixer.music.play()
                elif Presentation_Mode == '3':
                    g_presentation_mode = 'stabilize'
                    pygame.mixer.init()
                    pygame.mixer.music.load('/home/pi/yahboom-raspblock/StandardStart.mp3')
                    pygame.mixer.music.play()
            else:
                print("cmd-07 expression parse failure!")
        except:
            print('cmd-07 parse failure!')
            pass
    #Individual control of the mecanum wheels
    elif cmd_function == '08':
        reg = re.compile('^\$08,(?P<Wheel>[^ ]*),(?P<Wheel_speed>[^ ]*)#')
        regMatch = reg.match(cmd)                        
        try:
            if (regMatch != None):
                linebits = regMatch.groupdict()
                Wheel = linebits['Wheel']
                Wheel_speed = int(linebits['Wheel_speed'])
                print(Wheel_speed)
                if Wheel == '1':
                    Speed_WheelD = Wheel_speed
                elif Wheel == '2':
                    Speed_WheelC = Wheel_speed
                elif Wheel == '3':
                    Speed_WheelA = Wheel_speed
                elif Wheel == '4':
                    Speed_WheelB = Wheel_speed
            else:
                print("cmd-08 expression parse failure!")
        except:
            print('cmd-08 parse failure!')
            pass
    #Mecanum wheel overall control
    elif cmd_function == '09':
        reg = re.compile('^\$09,(?P<WheelA_speed>[^ ]*),(?P<WheelB_speed>[^ ]*),(?P<WheelC_speed>[^ ]*),(?P<WheelD_speed>[^ ]*)#')
        regMatch = reg.match(cmd)                        
        try:
            if (regMatch != None):
                linebits = regMatch.groupdict()
                Speed_WheelD = int(linebits['WheelA_speed'])   # Note the correspondence in the protocol documentation
                Speed_WheelC = int(linebits['WheelB_speed'])   
                Speed_WheelA = int(linebits['WheelC_speed'])   
                Speed_WheelB = int(linebits['WheelD_speed'])   

            else:
                print("cmd-09 expression parse failure!")
        except:
            print('cmd-09 parse failure!')
            pass
    #Buzzer control
    elif cmd_function == '10':
        reg = re.compile('^\$10,(?P<Buzzer_state>[^ ]*)#')
        regMatch = reg.match(cmd)                        
        try:
            if (regMatch != None):
                linebits = regMatch.groupdict()
                Buzzer_state = linebits['Buzzer_state']
                if Buzzer_state == '0':
                    robot.Buzzer_control(0)
                elif Buzzer_state == '1':
                    robot.Buzzer_control(1)
            else:
                print("cmd-10 expression parse failure!")
        except:
            print('cmd-10 parse failure!')
            pass
    #Autopilot control
    elif cmd_function == '11':
        reg = re.compile('^\$11,(?P<Auto_drive_state>[^ ]*)#')
        regMatch = reg.match(cmd)                        
        try:
            if (regMatch != None):
                linebits = regMatch.groupdict()
                Auto_drive_state = linebits['Auto_drive_state']
                if Auto_drive_state == '0':
                    g_auto_drive_switch = 'close'
#                     target_valuex = 1500
#                     target_valuey = 1500
#                     robot.Servo_control(target_valuex,target_valuey)
                elif Auto_drive_state == '1':
                    g_auto_drive_switch = 'open'
                    if updownpulse != 1500:
                        target_valuex = leftrightpulse
                        target_valuey = updownpulse  #Debugging by Sam Lau  2000  2100 
                    else:
                        target_valuex = 1550
                        target_valuey = 2050
                        leftrightpulse = target_valuex
                        updownpulse = target_valuey
                    robot.Servo_control(target_valuex,target_valuey)
                    print(leftrightpulse) # = target_valuex
                    print(updownpulse) # = target_valuey
            else:
                print("cmd-11 expression parse failure!")
        except:
            print('cmd-11 parse failure!')
            pass
    #Remote control maximum speed value setting
    elif cmd_function == '12':
        reg = re.compile('^\$12,(?P<Speed_kind>[^ ]*),(?P<Max_speed>[^ ]*)#')
        regMatch = reg.match(cmd)                        
        try:
            if (regMatch != None):
                linebits = regMatch.groupdict()
                Speed_kind = linebits['Speed_kind']
                Max_speed = int(linebits['Max_speed'])
                if Speed_kind == '1':
                    Max_speed_XY = Max_speed
                elif Speed_kind == '2':
                    Max_speed_Z = Max_speed
            else:
                print("cmd-12 expression parse failure!")
        except:
            print('cmd-12 parse failure!')
            pass
    #Position mode displacement setting
    elif cmd_function == '13':
        reg = re.compile('^\$13,X(?P<X_displacement>[^ ]*),Y(?P<Y_displacement>[^ ]*),Z(?P<Z_displacement>[^ ]*)#')
        regMatch = reg.match(cmd)                        
        try:
            if (regMatch != None):
                pygame.mixer.init()
                pygame.mixer.music.load('/home/pi/yahboom-raspblock/stabilizeStart.mp3') #位置模式已开启
                pygame.mixer.music.play()
                linebits = regMatch.groupdict()
                Position_disp_X = int(linebits['X_displacement'])
                Position_disp_Y = int(linebits['Y_displacement'])
                Position_disp_Z = int(linebits['Z_displacement'])
                g_presentation_mode = 'position'
                g_Position_update = 1
            else:
                print("cmd-13 expression parse failure!")
        except:
            print('cmd-13 parse failure!')
            pass
    #Function interface mode selection
    elif cmd_function == '14':
        reg = re.compile('^\$14,(?P<mode_select>[^ ]*)#')
        regMatch = reg.match(cmd)                        
        try:
            if (regMatch != None):
                linebits = regMatch.groupdict()
                mode_select = linebits['mode_select']
                if mode_select == '0':
                    g_mode = '0'
                    #Clear zero boundary status
                    g_servormode = '0'
                    g_robot_motion_mode = 'Free'
                    g_z_state = 'unlock'
                    g_presentation_mode = '0'
                    g_target_mode = '0'
                    g_tag_select = 'qrcode'
                    g_tag_identify_switch = 'close'
                    g_tag_brodcast_switch = 'close'
                    identify_tag = ''
                    last_identify_tag = ''
                    g_auto_drive_switch = 'close'
                    g_drive_view_switch = 0

                    Speed_axis_X = Speed_axis_Y = Speed_axis_Z = 0
                    Speed_WheelA = Speed_WheelB = Speed_WheelC = Speed_WheelD = 0
                    Position_disp_X = Position_disp_Y = Position_disp_Z = 0

                elif mode_select == '1':
                    g_mode = 'remote_control'
                    g_robot_motion_mode = 'Free'
                elif mode_select == '2':
                    g_mode = 'mecanum_control'
                elif mode_select == '3':
                    g_mode = 'presentation'
                elif mode_select == '4':
                    g_mode = 'target_track'
                    target_valuex = target_valuey = 1500
                    robot.Servo_control(target_valuex,target_valuey)
                elif mode_select == '5':
                    g_mode = 'tag_identification'
                    target_valuex = target_valuey = 1500
                    robot.Servo_control(target_valuex,target_valuey)
                elif mode_select == '6':
                    g_mode = 'voice_broadcast'
                elif mode_select == '7':
                    g_mode = 'auto_drive'
            else:
                print("cmd-14 expression parse failure!")
        except:
            print('cmd-14 parse failure!')
            pass
    #Remote control movement mode selection
    elif cmd_function == '15':
        reg = re.compile('^\$15,(?P<Remote_mode>[^ ]*)#')
        regMatch = reg.match(cmd)                        
        try:
            if (regMatch != None):
                linebits = regMatch.groupdict()
                Remote_mode = linebits['Remote_mode']
                if Remote_mode == '0':
                    g_robot_motion_mode = "Free"
                elif Remote_mode == '1':
                    g_robot_motion_mode = 'Stabilize'
            else:
                print("cmd-15 expression parse failure!")
        except:
            print('cmd-15 parse failure!')
            pass
    #Meanshift movement tracking parameter settings
    elif cmd_function == '16':
        reg = re.compile('^\$16,\((?P<X_value>[^ ]*),(?P<Y_value>[^ ]*)\),(?P<meanshint_switch>[^ ]*)#')
        regMatch = reg.match(cmd)                        
        try:
            if (regMatch != None):
                linebits = regMatch.groupdict()
                meanshint_switch =linebits['meanshint_switch']
                if meanshint_switch == '1':
                    meanshift_X = int(linebits['X_value'])
                    meanshift_Y = int(linebits['Y_value'])
                    meanshift_update_flag = 1
                    g_target_mode = 'meanshift_track'
                elif meanshint_switch == '0':
                    if g_target_mode == 'meanshift_track':
                        g_target_mode = '0'

            else:
                print("cmd-16 expression parse failure!")
        except:
            print('cmd-16 parse failure!')
            pass
    #Autopilot view switching
    elif cmd_function == '17':
        reg = re.compile('^\$17,(?P<view_switch>[^ ]*)#')
        regMatch = reg.match(cmd)                        
        try:
            if (regMatch != None):
                linebits = regMatch.groupdict()
                view_switch = linebits['view_switch']
                if view_switch == '1':
                    if g_drive_view_switch + 1 > 2:
                        g_drive_view_switch = 0
                    else:
                        g_drive_view_switch += 1
            else:
                print("cmd-17 expression parse failure!")
        except:
            print('cmd-17 parse failure!')
            pass
        
# Open the serial port
ser = serial.Serial("/dev/ttyAMA0", 115200)
ser.flushInput()
def Attitude_update():
    # Get receive buffer characters
    count = ser.inWaiting()
    if count != 0:
        recv = list(ser.read(count))
        recv = str(bytes(recv), encoding='UTF-8')
        if( recv.find("{A") != -1 and recv.find("}#") != -1 ):
            reg = re.compile('^{A(?P<Pitch>[^ ]*):(?P<Roll>[^ ]*):(?P<Yaw>[^ ]*):(?P<Voltage>[^ ]*)}#')
            regMatch = reg.match(recv)
            try:
                if (regMatch != None):
                    linebits = regMatch.groupdict()
                    temp = '$01,' + str(float(linebits['Voltage'])/100.0) + ',' + str(int(int(linebits['Roll'])/100)) + ',' +  str(int(int(linebits['Pitch'])/100)) + ',' + str(int(int(linebits['Yaw'])/100)) + ',#'
                    send_msg(g_socket, temp.encode('utf-8'))
            except:
                # print('Usart parse failure\r\n')
                pass
    # Emptying the receive buffer
    ser.flushInput()

#Campaign status refresh process
def motion_refresh():
    global Speed_axis_X,Speed_axis_Y,Speed_axis_Z
    global Speed_WheelA, Speed_WheelB, Speed_WheelC, Speed_WheelD
    global Position_disp_X, Position_disp_Y, Position_disp_Z
    global Max_speed_XY, Max_speed_Z
    global g_servormode, g_mode, g_robot_motion_mode, g_z_state, g_presentation_mode, g_Position_update
    #Sport mode for small cars
    #0 -> Speed mode | 1 -> Position mode
    run_mode = 0

    delay_count = 0
    while 1:
        if g_mode == 'presentation' and g_presentation_mode == 'position':
            if run_mode != 1:
                robot.PID_Mode_control(1, 200, 150, 20, 0, 20, 12, 2, 5)
                run_mode = 1
        else:
            if run_mode != 0:
                robot.PID_Mode_control(0, 200, 150, 20, 0, 20, 12, 2, 5)
                run_mode = 0
        if g_mode == 'remote_control' or g_mode == 'mecanum_control':
            if Speed_axis_X != 0 or Speed_axis_Y != 0 or Speed_axis_Z != 0:
                if g_z_state == 'unlock':
                    robot.Speed_axis_control(Speed_axis_X, Speed_axis_Y, Speed_axis_Z)
                elif g_z_state == 'lock':
                    if g_robot_motion_mode == 'Free':
                        robot.Speed_axis_control(Speed_axis_X, Speed_axis_Y, Speed_axis_Z)
                    elif g_robot_motion_mode == 'Stabilize':
                        robot.Speed_axis_Yawhold_control(Speed_axis_X, Speed_axis_Y)
            elif Speed_WheelA != 0 or Speed_WheelB != 0 or Speed_WheelC != 0 or Speed_WheelD != 0:
                robot.Speed_Wheel_control(Speed_WheelA,Speed_WheelB,Speed_WheelC,Speed_WheelD)
            
            if g_servormode == 'servo_forward':
                camUpFunction(3)
            elif g_servormode == 'servo_down':
                camDownFunction(3)
            elif g_servormode == 'servo_left':
                camLeftFunction(3)
            elif g_servormode == 'servo_right':
                camRightFunction(3)
            elif g_servormode=='servo_init':
                g_servormode = '0'
                camservoInitFunction()
        elif g_mode == 'presentation':
            #print("1")
            if g_presentation_mode == 'around':
                print("around")
                for i in range(1, 2000):
                    robot.Speed_Wheel_control(-5, 20, -20, 5)    #Right pan  
                
                robot.Speed_Wheel_control(0, 0, 0, 0)    #Stop
                time.sleep(2)
                
            elif g_presentation_mode == 'translation':
                print("translation")
                for i in range(1, 1000):
                    robot.Speed_Wheel_control(-8, 8, -8, 8)    #Right pan
                robot.Speed_Wheel_control(0, 0, 0, 0)      #Stop
                time.sleep(2)
                for i in range(1, 1000):
                    robot.Speed_Wheel_control(-8, -8, -8, -8)  #Speed of all wheels backwards 2
                robot.Speed_Wheel_control(0, 0, 0, 0)      #Stop
                time.sleep(2)
                for i in range(1, 1000):
                    robot.Speed_Wheel_control(8, -8, 8, -8)    #Left pan
                robot.Speed_Wheel_control(0, 0, 0, 0)      #Stop
                time.sleep(2)
                for i in range(1, 1000):
                    robot.Speed_Wheel_control(8, 8, 8, 8)      #Speed of all wheels backwards 2
                robot.Speed_Wheel_control(0, 0, 0, 0)      #Stop
                time.sleep(2)
        
                robot.Speed_Wheel_control(0, 0, 0, 0)      #Stop
                time.sleep(5)
            elif g_presentation_mode == 'stabilize':
                robot.Speed_axis_Yawhold_control(0, 0)
            elif g_presentation_mode == 'position':
                if g_Position_update == 1:
                    robot.Position_disp_control(Position_disp_X, Position_disp_Y, Position_disp_Z)
                    g_Position_update = 0
        elif g_mode == "auto_drive":
            if g_servormode == 'servo_forward':
                camUpFunction(1)
            elif g_servormode == 'servo_down':
                camDownFunction(1)
            elif g_servormode == 'servo_left':
                camLeftFunction(1)
            elif g_servormode == 'servo_right':
                camRightFunction(1)
            elif g_servormode=='servo_init':
                g_servormode = '0'
                camservoInitFunction()
        else:
            time.sleep(0.01)
        delay_count += 1
        if delay_count >= 10:
            delay_count = 0
            Attitude_update()
        time.sleep(0.01)

motion_refresh_id = threading.Thread(target=motion_refresh)
motion_refresh_id.setDaemon(True)
motion_refresh_id.start()

#Tensorflow AI object recognition initialization
# Init tf model
MODEL_NAME = '/home/pi/yahboom-raspblock/ssdlite_mobilenet_v2_coco_2018_05_09' #fast
PATH_TO_CKPT = MODEL_NAME + '/frozen_inference_graph.pb' 
PATH_TO_LABELS = '/home/pi/yahboom-raspblock/data/mscoco_label_map.pbtxt' #os.path.join('data', 'mscoco_label_map.pbtxt') 
NUM_CLASSES = 90 
IMAGE_SIZE = (12, 8) 
fileAlreadyExists = os.path.isfile(PATH_TO_CKPT) 

if not fileAlreadyExists:
    print('Model does not exsist !')
    exit

# LOAD GRAPH
print('Loading Graph...')
detection_graph = tf.Graph() 
with detection_graph.as_default(): 
    od_graph_def = tf.compat.v1.GraphDef()
    with tf.io.gfile.GFile(PATH_TO_CKPT, 'rb') as fid: 
        serialized_graph = fid.read() 
        od_graph_def.ParseFromString(serialized_graph) 
        tf.import_graph_def(od_graph_def, name='')
label_map = label_map_util.load_labelmap(PATH_TO_LABELS) 
categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES, use_display_name=True) 
category_index = label_map_util.create_category_index(categories)
print('Finish Load Graph..')

### End of initialization of Tensorflow AI object recognition

### Filter the signal with a window size of window_size
### Require signal to be a list
def gen(l, window_size):
    index = 0
    ans = 0
    times = 0
    while True:
        while index < window_size:
            ans += l[times + index]
            index += 1
        yield float(ans) / float(window_size)
        ###Reset
        index = 0
        ans = 0
        times += 1
def mean_filter(signal, window_size):
    window_size =8
    temp = gen(signal, window_size)
    filtered = []
    for i in range(len(signal) - window_size):
        filtered.append(next(temp))
    return filtered
def find_peak(filtered_signal, length_data, thre, peak_width):
    l=[];
    for i in range(1, length_data - 1): # Find the extremes over the entire length of B
        if (filtered_signal[i - 1] < filtered_signal[i] and filtered_signal[i] > filtered_signal[i + 1]
    and filtered_signal[i] > thre): # Find the extreme values and set the threshold, here the threshold is set to 20
            l.append(i) # Find the location of the extremes
        elif (filtered_signal[i] == filtered_signal[i - 1] and filtered_signal[i] > thre):
            l.append(i) # There may be equivalence around the highest point
    CC = len(l) # How many statistical extremes are there, two if there are two lines, and only one if there is one
    cou = 0
    for j in range(1, CC):
        if l[j] - l[j - 1] < peak_width: # This judgement is used to remove extreme points that lie within the same peak
            cou = cou + 1
    rcou = CC - cou
    return rcou

def bgr8_to_jpeg(value, quality=75):
    return bytes(cv2.imencode('.jpg', value)[1])

# Running programs based on state machines contains video stream returns
def mode_handle():
    global color_lower, color_upper
    global g_tag_identify_switch, g_tag_brodcast_switch
    global g_mode, g_socket, g_target_mode, g_tag_select, g_presentation_mode
    global face_x, face_y, face_w, face_h
    global target_valuex, target_valuey
    global meanshift_X, meanshift_Y, meanshift_width, meanshift_high, meanshift_update_flag
    global g_auto_drive_switch, g_drive_view_switch
    global run_mode

    face_x = face_y = face_w = face_h = 0
    color_x = color_y = color_radius = 0
    
    identify_tag = ''
    last_identify_tag = ''
    object_count = 0
    object_brodcast_delay = 0
    t_start = time.time()
    fps = 0

    window_size = 8
    thre = 1300 #Threshold height of the peak, only peaks above this value are considered a peak, otherwise they are considered noise fluctuations, it is recommended that this value is above the average value
    peak_width = 20 # To avoid several spikes within a peak that could be identified as multiple peaks, the width of the peak is set here and all peaks within this width are considered to be the same.

#     matSrc = np.float32([[0, 149],  [310, 149], [271, 72], [43, 72]])
#     matDst = np.float32([[100,240], [200,240], [200,0], [100,0]])
    
    # liusen fix 20200319
    #matSrc = np.float32([[0, 149],  [320, 149], [271, 72], [43, 72]]) #310-320
    #matDst = np.float32([[0,240], [320,240], [310,0], [0,0]])          #310-320
    matSrc = np.float32([[0, 149],  [310, 149], [271, 72], [43, 72]]) #310-320
    matDst = np.float32([[0,240], [310,240], [310,0], [0,0]])          #310-320
    #matDst = np.float32([[0,149], [310,149], [310,72], [0,72]])
    
    matAffine = cv2.getPerspectiveTransform(matSrc,matDst)# mat 1 src 2 dst
     #src 4->dst 4 (bottom left corner bottom right corner top right corner top left corner)
    pts = np.array([[0, 149],  [310, 149], [271, 72], [43, 72]], np.int32)


    g_camera = cv2.VideoCapture(0)
    g_camera.set(3, 320)
    g_camera.set(4, 240)
    g_camera.set(5, 120)  #Set the frame rate
    g_camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))
    g_camera.set(cv2.CAP_PROP_BRIGHTNESS, 40) #set brightness -64 - 64 0.0
    g_camera.set(cv2.CAP_PROP_CONTRAST, 50) #set contrast -64 - 64 2.0
    g_camera.set(cv2.CAP_PROP_EXPOSURE, 156) #set exposure value 1.0 - 5000 156.0    retval, frame = g_camera.read()
    imgencode = cv2.imencode('.jpg', frame)[1]

    xservo_pid = PID.PositionalPID(1.1, 0.2, 0.8)
    yservo_pid = PID.PositionalPID(0.8, 0.2, 0.8)
    #Autopilot steering angle PID
    Z_axis_pid = PID.PositionalPID(0.7, 0.00, 1.8) #PID.PositionalPID(1.2, 0, 0.1) 0.85 0 0.3
    
    
    #Face recognition classifier file
    face_haar = cv2.CascadeClassifier("/home/pi/yahboom-raspblock/haarcascade_profileface.xml")
    
    #Object recognition session
    sess =  tf.compat.v1.Session(graph=detection_graph)
    
    camservoInitFunction()

    # Meanshift initialization for boot run
    retval, frame = g_camera.read()
    # Set the initial position of the window
    track_window = (meanshift_X, meanshift_Y, meanshift_width, meanshift_high)
    # Create the ROI for the track 
    roi = frame[meanshift_Y:meanshift_Y+meanshift_high, meanshift_X:meanshift_X+meanshift_width]
    # frame = cv2.rectangle(frame, (140,100), (180,140), 255,2)
    # Convert image from RGB space to HSV space
    hsv_roi = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    # Ignore the low luminance values 
    mask = cv2.inRange(hsv_roi, np.array((0., 60.,32.)), np.array((180.,255.,255.)))
    # Calculate image histogram
    roi_hist = cv2.calcHist([hsv_roi],[0],mask,[180],[0,180])
    #Normalize
    cv2.normalize(roi_hist,roi_hist,0,255,cv2.NORM_MINMAX)
    # Set termination criteria, 10 iterations or at least 1 pt shift
    term_crit = ( cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1 )
    robot.BoardData_Get(0) # Enables automatic data reporting
    
    while 1:
        if g_mode == 'auto_drive':
            if g_camera.get(cv2.CAP_PROP_FRAME_WIDTH) != 1920:
                print('################# 0 1920*1080')
                g_camera.release()
                print('################# 1 1920*1080')
                g_camera = cv2.VideoCapture(0)
                print('################# 2 1920*1080')
                g_camera.set(3, 1920)
                g_camera.set(4, 1080)
                g_camera.set(5, 30) # Set the frame rate
                g_camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))
                g_camera.set(cv2.CAP_PROP_BRIGHTNESS, 40) # set brightness -64 - 64 0.0
                g_camera.set(cv2.CAP_PROP_CONTRAST, 50) #set contrast -64 - 64 2.0
                g_camera.set(cv2.CAP_PROP_EXPOSURE, 156) #set exposure value 1.0 - 5000 156.0
                print('################# 3 1920*1080')
        else:
            if g_camera.get(cv2.CAP_PROP_FRAME_WIDTH) != 320:
                print('################# 0 320*240')
                g_camera.release()
                print('################# 1 320*240')
                g_camera = cv2.VideoCapture(0)
                print('################# 2 320*240')
                g_camera.set(3, 320)
                g_camera.set(4, 240)
                g_camera.set(5, 120)  #Set the frame rate
                g_camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))
                g_camera.set(cv2.CAP_PROP_BRIGHTNESS, 40) #Set brightness -64 - 64  0.0
                g_camera.set(cv2.CAP_PROP_CONTRAST, 50)   #Setting the contrast -64 - 64  2.0
                g_camera.set(cv2.CAP_PROP_EXPOSURE, 156)  #Setting exposure values 1.0 - 5000  156.0
                print('################# 3 320*240')
        
        retval, frame = g_camera.read()
        if retval == False:  #Preventing failure to read the correct video image
            print('read camera err!')
            continue
        #############
        
        fps = fps + 1
        mfps = fps / (time.time() - t_start)
        #cv2.putText(img, str(i), (123,456)), font, 2, (0,255,0), 3) 
        #The parameters are, in order: image, added text, top left corner coordinates, font, font size, colour, font thickness
        if g_mode == 'target_track':
            if g_target_mode == 'face_track':
                # Converting images to black and white
                gray_img = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_haar.detectMultiScale(gray_img, 1.1, 3)
                if len(faces)>0:
                    (face_x, face_y, face_w, face_h) = faces[0]
                    # cv2.rectangle(frame,(face_x+10,face_y),(face_x+face_w-10,face_y+face_h+20),(0,255,0),2)
                    cv2.rectangle(frame,(face_x,face_y),(face_x+face_w,face_y+face_h),(0,255,0),2)

                    #Proportion-Integration-Differentiation算法
                    # Input of X-axis direction parameters PID control input
                    xservo_pid.SystemOutput = face_x+face_w/2
                    xservo_pid.SetStepSignal(150)
                    xservo_pid.SetInertiaTime(0.01, 0.1)
                    target_valuex = int(1500 + xservo_pid.SystemOutput)
                    # Input PID control input for Y-axis direction parameters
                    yservo_pid.SystemOutput = face_y+face_h/2
                    yservo_pid.SetStepSignal(120)
                    yservo_pid.SetInertiaTime(0.01, 0.1)
                    target_valuey = int(1500 - yservo_pid.SystemOutput)
                    # Turning the head to the PID adjustment position
                    robot.Servo_control(target_valuex,target_valuey)
            elif g_target_mode == 'color_track':
                frame_=cv2.GaussianBlur(frame,(5,5),0)                    
                hsv=cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)
                mask=cv2.inRange(hsv,color_lower,color_upper)  
                mask=cv2.erode(mask,None,iterations=2)
                mask=cv2.dilate(mask,None,iterations=2)
                mask=cv2.GaussianBlur(mask,(3,3),0)     
                cnts=cv2.findContours(mask.copy(),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)[-2] 
                if len(cnts)>0:
                    cnt = max (cnts,key=cv2.contourArea)
                    (color_x,color_y),color_radius=cv2.minEnclosingCircle(cnt)
                    if color_radius > 10:
                        # Mark the detected colours
                        cv2.circle(frame,(int(color_x),int(color_y)),int(color_radius),(255,0,255),2)  
                        #Proportion-Integration-Differentiation
                        xservo_pid.SystemOutput = color_x
                        xservo_pid.SetStepSignal(150)
                        xservo_pid.SetInertiaTime(0.01, 0.1)
                        target_valuex = int(1500+xservo_pid.SystemOutput)
                        # Input PID control input for Y-axis direction parameters
                        yservo_pid.SystemOutput = color_y
                        yservo_pid.SetStepSignal(150)
                        yservo_pid.SetInertiaTime(0.01, 0.1)
                        target_valuey = int(1500-yservo_pid.SystemOutput)
                        # Turning the head to the PID adjustment position
                        robot.Servo_control(target_valuex,target_valuey)
            elif g_target_mode == 'meanshift_track':
                if meanshift_update_flag == 1:
                    print('Meanshift init!')
                    # Set the initial position of the window
                    track_window = (meanshift_X, meanshift_Y, meanshift_width, meanshift_high)
                    # Create the ROI for the track 
                    roi = frame[meanshift_Y:meanshift_Y+meanshift_high, meanshift_X:meanshift_X+meanshift_width]
                    frame = cv2.rectangle(frame, (140,100), (180,140), 255,2)
                    # image converted from RGB space to HSV space
                    hsv_roi = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                    # Ignore the low luminance values 
                    mask = cv2.inRange(hsv_roi, np.array((0., 60.,32.)), np.array((180.,255.,255.)))
                    # Calculate image histogram
                    roi_hist = cv2.calcHist([hsv_roi],[0],mask,[180],[0,180])
                    #Normalize
                    cv2.normalize(roi_hist,roi_hist,0,255,cv2.NORM_MINMAX)
                    # Set termination criteria, 10 iterations or at least 1 pt shift
                    term_crit = ( cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1 )
                    meanshift_update_flag = 0
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                dst = cv2.calcBackProject([hsv],[0],roi_hist,[0,180],1)
                # apply meanshift to get the new location
                ret, track_window = cv2.meanShift(dst, track_window, term_crit)
                # Draw it on image
                x,y,w,h = track_window
                cv2.rectangle(frame, (x,y), (x+w,y+h), 255,2)
        elif g_mode == 'tag_identification':
            if g_tag_identify_switch == 'open':
                if g_tag_select == 'qrcode':
                    gray_img = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    barcodes = pyzbar.decode(gray_img)
                    for barcode in barcodes:
                        # Extract the position of the bounding box of the QR code
                        # Draw the bounding box of the barcode in the image
                        (x, y, w, h) = barcode.rect
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 225, 0), 2)
                        # Extract the QR code data as a byte object, so if we want to draw on the output image
                        # draw it, we need to convert it to a string first
                        barcodeData = barcode.data.decode("utf-8")
                        barcodeType = barcode.type
                        # Plot the data and barcode type of the barcode on the image
                        text = "{} ({})".format(barcodeData, barcodeType)
                        cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,0.5, (225, 225, 0), 2)
                        # Print barcode data and barcode type to the terminal
                        # print("[INFO] Found {} barcode: {}".format(barcodeType, barcodeData))
                        identify_tag = barcodeData
                        if identify_tag != '':
                            identify_tag = 'The Message is ' + identify_tag
                elif g_tag_select == 'object':
                    image_np_expanded = np.expand_dims(frame, axis=0) 
                    image_tensor = detection_graph.get_tensor_by_name('image_tensor:0') 
                    detection_boxes = detection_graph.get_tensor_by_name('detection_boxes:0') 
                    detection_scores = detection_graph.get_tensor_by_name('detection_scores:0') 
                    detection_classes = detection_graph.get_tensor_by_name('detection_classes:0') 
                    num_detections = detection_graph.get_tensor_by_name('num_detections:0')
                    
                    # print('Running detection..') 
                    (boxes, scores, classes, num) = sess.run( 
                        [detection_boxes, detection_scores, detection_classes, num_detections], 
                        feed_dict={image_tensor: image_np_expanded}) 
            
                    # print('Done.  Visualizing..') 
                    vis_utils.visualize_boxes_and_labels_on_image_array(
                            frame,
                            np.squeeze(boxes),
                            np.squeeze(classes).astype(np.int32),
                            np.squeeze(scores),
                            category_index,
                            use_normalized_coordinates=True,
                            line_thickness=8)
                    for i in range(0, 10):
                        if scores[0][i] >= 0.4:
                            if i == 0:
                                identify_tag = ''
                            if identify_tag == '':
                                identify_tag = identify_tag + category_index[int(classes[0][i])]['name']
                            else:
                                identify_tag = identify_tag + ' and ' + category_index[int(classes[0][i])]['name']
                    if identify_tag != '':
                        identify_tag = 'I Find ' + identify_tag
                elif g_tag_select == 'gesture':
                    """ 2.调用手势识别 """
                    #Logger('error.log', level='error').logger.error('gesture1')
                    raw = str(client_body.gesture(bgr8_to_jpeg(frame)))
                    #Logger('error.log', level='error').logger.error('gesture2')
                    text = demjson.decode(raw)
                    #Logger('error.log', level='error').logger.error(text)
                    try:
                        res = text['result'][0]['classname']
                    except:
                        #Logger('error.log', level='error').logger.error('Not recognised')
                        #print('Result: Nothing recognized~' )
                        # 1 dst 2 text content 3 coordinates 4 5 font size 6 color 7 thickness 8 line type
                        # cv2.putText(frame, 'unidentification', (250,30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,200), 2, cv2.LINE_AA) # Only English can be displayed
                        # cv2.putText(frame, 'unidentification', (10,80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,200), 2, cv2.LINE_AA) #English only
                        frame = cv2ImgAddText(frame, "Not recognised", 10, 30, (0, 0 , 255), 30)
                        info = "Not recognised"
                    else:
                        #print('Identification results:' + hand[res])
                        info = hand[res]
                        #Logger('error.log', level='error').logger.error(info)
                        #cv2.putText(frame, hand[res], (250,30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,0), 2, cv2.LINE_AA)
                        frame = cv2ImgAddText(frame, hand[res], 10, 30, (0, 255 , 0), 30)  #中文
                        #cv2.putText(frame, res, (10,80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,200), 2, cv2.LINE_AA) #English only   
                    
                        identify_tag = info
                        if identify_tag != '':
                            identify_tag = identify_tag
                
                if g_tag_brodcast_switch == 'open':
                    if identify_tag != '':
                        if identify_tag != last_identify_tag:
                            if g_tag_select == 'object':
                                object_brodcast_delay += 1
                                if object_brodcast_delay >= 8:
                                    result = client.synthesis(text = identify_tag, 
                                    options={'spd':3,'vol':15,'per':2,})
                                    #Writing the synthesised speech to a file
                                    if not isinstance(result,dict):
                                        with open('/home/pi/yahboom-raspblock/audio.mp3','wb') as f:
                                            f.write(result)
                                            #We use the pygame that comes with the Raspberry Pi
                                            pygame.mixer.init()
                                            pygame.mixer.music.load('/home/pi/yahboom-raspblock/audio.mp3')
                                            pygame.mixer.music.play()
                                            last_identify_tag = identify_tag
                                    else:
                                        print(result)
                                    object_brodcast_delay = 0
                            elif g_tag_select == 'qrcode' or g_tag_select == 'gesture':
                                result = client.synthesis(text = identify_tag, 
                                    options={'spd':3,'vol':15,'per':2,})
                                #Writing the synthesised speech to a file
                                if not isinstance(result, dict):
                                    with open('/home/pi/yahboom-raspblock/audio.mp3','wb') as f:
                                        f.write(result)
                                        #We use the pygame that comes with the Raspberry Pi
                                        pygame.mixer.init()
                                        pygame.mixer.music.load('/home/pi/yahboom-raspblock/audio.mp3')
                                        pygame.mixer.music.play()
                                        last_identify_tag = identify_tag
                                else:
                                    print(result)
        elif g_mode == 'auto_drive':
            frame = cv2.resize(frame,(320,240))
            #frame = cv2.GaussianBlur(frame,(5,5),0)
            dst = cv2.warpPerspective(frame,matAffine,(320,240))
            # of vertices: 4, matrix becomes 4*1*2 dimensional
            # OpenCV needs to turn a polygon's vertex coordinates into a matrix of vertices x 1 x 2 dimensions
            # The first parameter of the reshape is -1, which means "arbitrary", meaning that the value of this dimension is calculated based on the later dimensions
            pts = pts.reshape((-1, 1, 2))
            cv2.polylines(frame, [pts],True, (255, 0, 0), 3)

            dst_gray = cv2.cvtColor(dst, cv2.COLOR_RGB2GRAY)
            dst_retval, dst_binaryzation = cv2.threshold(dst_gray, 128, 255, cv2.THRESH_BINARY) # 100->120  Threshold setting
            dst_binaryzation = cv2.erode(dst_binaryzation, None, iterations=1)
            histogram = np.sum(dst_binaryzation[dst_binaryzation.shape[0]//2:,:], axis=0)
            midpoint = np.int(histogram.shape[0]/2)
            
#             leftx_base = np.argmax(histogram[:midpoint],axis = 0)
#             rightx_base = np.argmax(histogram[midpoint:],axis = 0) + midpoint

#             leftx_base_value = np.max(histogram[:midpoint],axis = 0)
#             rightx_base_value = np.max(histogram[midpoint:],axis = 0)
            leftx_base = np.argmin(histogram[:midpoint],axis = 0) + 5              #Plus the width of the black line
            rightx_base = np.argmin(histogram[midpoint:],axis = 0) + midpoint + 5  #Plus the width of the black line

#             leftx_base_value = np.min(histogram[:midpoint],axis = 0)
#             rightx_base_value = np.min(histogram[midpoint:],axis = 0)

#             if leftx_base < 100:
#                 leftx_base = 100
#             if rightx_base > 200:
#                 rightx_base = 200
#             elif rightx_base == 160:
#                 rightx_base = 200
            # add liusen 20200319
#             if leftx_base < 5:
#                 leftx_base = 5
#             if rightx_base > 315:
#                 rightx_base = 315
            if leftx_base < 10:
                leftx_base = 10
            if rightx_base > 300:
                rightx_base = 300
            if leftx_base > 140 or rightx_base - leftx_base < 50:
                leftx_base = 10
            if rightx_base < 159 or rightx_base - leftx_base < 50:
                rightx_base = 300

            histogram = np.sum(dst_binaryzation[dst_binaryzation.shape[0]//2:,:], axis=0)
            dst_binaryzation = cv2.cvtColor(dst_binaryzation,cv2.COLOR_GRAY2RGB)
            cv2.line(dst_binaryzation,(154,0),(154,240),(255,0,255),2) # 149-159 fix liusen 200323
            lane_center = int((leftx_base + rightx_base)/2)
            cv2.line(dst_binaryzation,(leftx_base,0),(leftx_base,240),(0,255,0),2)
            cv2.line(dst_binaryzation,(rightx_base,0),(rightx_base,240),(0,255,0),2)
            cv2.line(dst_binaryzation,(lane_center,0),(lane_center,240),(255,0,0),2)
            Bias = 154 - lane_center  # 149-159 fix liusen 200323
            

            if(Bias > 30):
                Bias = 30
            elif Bias < -30:
                Bias = -30
                
            #PID adjustment of steering angle
            Z_axis_pid.SystemOutput = Bias
            Z_axis_pid.SetStepSignal(0)
            Z_axis_pid.SetInertiaTime(0.5, 0.2)

            if Z_axis_pid.SystemOutput > 30:
                Z_axis_pid.SystemOutput = 30
            elif Z_axis_pid.SystemOutput < -30:
                Z_axis_pid.SystemOutput = -30

            #filtered_signal = mean_filter(histogram, window_size)
            #length_data = len(filtered_signal)
            #peaks_count = find_peak(filtered_signal, length_data, thre, peak_width)
            
            if g_auto_drive_switch == 'open':
#                 if peaks_count == 2 or peaks_count == 4:
                robot.Speed_axis_control(0,5,int(Z_axis_pid.SystemOutput)) # +3
#                 elif peaks_count == 1:
#                     if leftx_base_value == 0 or (rightx_base_value > leftx_base_value):
#                         # robot.Speed_axis_control(0,5,abs(int(Z_axis_pid.SystemOutput))+3,0,0,0)
#                         # robot.Speed_axis_control(0,5,-12)
#                         robot.Speed_axis_control(0,5,-15)
#                     elif rightx_base_value == 0 or (leftx_base_value > rightx_base_value):
#                         # robot.Speed_axis_control(0,5,int(Z_axis_pid.SystemOutput)+3,0,0,1)
#                         # robot.Speed_axis_control(0,5,12)
#                         robot.Speed_axis_control(0,5,15)

#                 elif peaks_count == 3:
#                     robot.Speed_axis_control(0, 5, 0)
            if g_drive_view_switch == 0:
                cv2.putText(frame, "FPS:  " + str(int(mfps)), (10, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                imgencode = cv2.imencode('.jpg', frame)[1]
            elif g_drive_view_switch == 1:
                cv2.putText(dst, "FPS:  " + str(int(mfps)), (10, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                imgencode = cv2.imencode('.jpg', dst)[1]
            elif g_drive_view_switch == 2:
                cv2.putText(dst_binaryzation, "FPS:  " + str(int(mfps)), (10,15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255), 2)
                cv2.putText(dst_binaryzation, "Bias: " + str(int(Bias)), (10,35), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255), 2)
                #cv2.putText(dst_binaryzation, "Peaks: " + str(int(peaks_count)), (10,55), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255), 2)
                cv2.putText(dst_binaryzation, "L_peak: " + str(int(leftx_base)), (10,75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255), 2)
                cv2.putText(dst_binaryzation, "R_peak: " + str(int(rightx_base)), (10, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
                imgencode = cv2.imencode('.jpg', dst_binaryzation)[1]
#         elif g_mode == 'presentation':
#             print("1")
#             if g_presentation_mode == 'around':
#                 print("around")
#                 robot.Speed_Wheel_control(-8, -15, 15, 8)    #Right surround
#                 time.sleep(5)
#                 robot.Speed_Wheel_control(0, 0, 0, 0)    #Stop
#                 time.sleep(5)
#                 robot.Speed_Wheel_control(8, 15, -15, -8)    #Left surround
#                 time.sleep(5)
#                 robot.Speed_Wheel_control(0, 0, 0, 0)    #Stop
#                 time.sleep(5)
#             elif g_presentation_mode == 'translation':
#                 print("translation")
#                 robot.Speed_Wheel_control(-8, -8, 8, 8)    #Right-handed
#                 time.sleep(2)
#                 robot.Speed_Wheel_control(-8, -8, -8, -8)  #Speed of all wheels backwards 2
#                 time.sleep(2)
#                 robot.Speed_Wheel_control(8, 8, -8, -8)    #L-alpha
#                 time.sleep(2)
#                 robot.Speed_Wheel_control(8, 8, 8, 8)      #Speed of all wheels forward 2
#                 time.sleep(2)
#                 robot.Speed_Wheel_control(0, 0, 0, 0)      #Stop
#                 time.sleep(5)
        
        if g_mode != 'auto_drive':
            cv2.putText(frame, "FPS:  " + str(int(mfps)), (10,20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255), 2)
            imgencode = cv2.imencode('.jpg', frame)[1]
        
        imgencode = imgencode.tostring()
        yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + imgencode + b'\r\n')

        # time.sleep(0.01)
        # time.sleep(0.005)
        time.sleep(0.006)
    del(camera)
    robot.BoardData_Get(9)  #Turn off automatic data reporting
        
if __name__ == '__main__':
    robot.Buzzer_control(1)
    time.sleep(0.1)
    robot.Buzzer_control(0)
    time.sleep(0.2)
    robot.Buzzer_control(1)
    time.sleep(0.1)
    robot.Buzzer_control(0)
    time.sleep(0.2)
    robot.Buzzer_control(1)
    time.sleep(0.1)
    robot.Buzzer_control(0)
    time.sleep(0.2)
    pygame.mixer.init()
    pygame.mixer.music.load('/home/pi/yahboom-raspblock/start.mp3')
    pygame.mixer.music.play()

    app.run(host='0.0.0.0', port=6001, debug=False, use_reloader = False)
    