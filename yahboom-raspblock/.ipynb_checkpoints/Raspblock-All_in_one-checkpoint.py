'''
@Copyright (C): 2010-2019, Shenzhen Yahboom Tech
@Author: Malloy.Yuan
@Date: 2019-08-02 12:03:42
@LastEditors  : Malloy.Yuan
@LastEditTime : 2020-01-17 16:43:03
'''

from flask import Flask, render_template, Response
from importlib import import_module
import os, serial, socket, base64, hashlib, sys, struct, threading, hashlib, re, time, cv2, PID, pygame
import numpy as np
from Raspblock import Raspblock
from aip import AipSpeech
import pyzbar.pyzbar as pyzbar
from PIL import Image
import tensorflow as tf
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_utils



""" 你的 APPID AK SK """
APP_ID = '17852430'
API_KEY = 'eGeO4iQGAjHCrzBTYd1uvTtf'
SECRET_KEY = 'Cn1EVsUngZDbRLv4OxAFrDHSo8PsvFVP'
# 新建一个AipSpeech
client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)

#界面功能模式状态机
# 0 -> 功能选择主界面(0) | 1 -> 遥控界面(remote_control) | 2 -> 麦克纳姆轮控制界面(mecanum_control) | 3 -> 模式演示界面(presentation) | 4 -> 目标追踪界面(target_track) | 5 -> 标签识别界面(tag_identification) | 6 -> 语音播报界面(voice_broadcast) | 7 -> 自动驾驶界面(auto_drive)
global g_mode
g_mode = '0'

#遥控界面(remote_control) -- 舵机运动模式子状态机
# 1-6(上(servo_forward)|下(servo_down)|左(servo_left)|右(servo_right)|停(0)|归中(servo_init))
global g_servormode
g_servormode = '0'

#遥控界面(remote_control) -- 运动模式子状态机
# 0(Free) | 1(Stabilize) 
global g_robot_motion_mode
g_robot_motion_mode = 'Free'  # Stabilize / Free

#遥控界面(remote_control) -- 偏航角改变子状态机
# unlock / lock
global g_z_state
g_z_state = 'unlock'  # unlock / lock

#模式演示界面(presentation) -- 演示模式子状态机
# 0 - > 演示模式选择主界面(0) |   1 - > 环绕模式(around) |  2 - > 平移模式(translation) |  3 - > 自稳模式(stabilize) |  4 - > 位置模式(position)
global g_presentation_mode
g_presentation_mode = '0'

#模式演示界面(presentation) -- 演示模式子状态机
# 0 - > 不更新值 |   1 - > 更新值
global g_Position_update
g_Position_update = 0

#目标追踪界面(target_track) -- 追踪模式子状态机
# 0 | face_track | color_track | meanshift_track
global g_target_mode
g_target_mode = '0'

#标签识别界面(tag_identification) -- 识别模式子状态机
# 1 -> 二维码识别(qrcode) | 2 -> 对象检测(object)
global g_tag_select
g_tag_select = 'qrcode'

#标签识别界面(tag_identification) -- 识别开关子状态机
# 0 -> 关(close) | 1 -> 开(open)
global g_tag_identify_switch
g_tag_identify_switch = 'close'

#标签识别界面(tag_identification) -- 识别播报开关子状态机
# 0 -> 关(close) | 1 -> 开(open)
global g_tag_brodcast_switch
g_tag_brodcast_switch = 'close'

#自动驾驶界面(auto_drive) -- 自动驾驶开关子状态机
# 0 -> 关(close) | 1 -> 开(open)
global g_auto_drive_switch
g_auto_drive_switch = 'close'

#自动驾驶界面(auto_drive) -- 自动驾驶画面切换子状态机
# 0 -> 初始画面(origin_view) | 1 -> 鸟瞰画面(bird_view) | 2 -> 循迹画面(Lane_view)
global g_drive_view_switch
g_drive_view_switch = 0

#运动过程变量
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

#移动追踪参数设置变量
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

global config_ip,config_left_speed,config_right_speed
config_file = open("config.txt", "r")
lines = config_file.readlines()  #按行读取文件中所有内容
pattern = re.compile('"(.*)"')
config_ip = pattern.findall(lines[0])
print('IP地址: %s'%config_ip[0])
config_file.close()

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
        tid=threading.Thread(target=start_tcp_server, args=(config_ip[0],6000,))
        tid.setDaemon(True)
        tid.start()
    print('init websocket!!!!!!!!!')
    return render_template('init.html')

'''以下是舵机控制的部分    '''
def camUpFunction():
    global updownpulse
    updownpulse-=3
    if updownpulse>2500:
        updownpulse=2500
    robot.Servo_control(leftrightpulse, updownpulse)

def camDownFunction():
    global updownpulse
    updownpulse+=3
    if updownpulse<500:
        updownpulse=500
    robot.Servo_control(leftrightpulse, updownpulse)

def camLeftFunction():
    global leftrightpulse
    leftrightpulse+=3
    if leftrightpulse>2500:
        leftrightpulse=2500
    robot.Servo_control(leftrightpulse, updownpulse)

def camRightFunction():
    global leftrightpulse
    leftrightpulse-=3
    if leftrightpulse<500:
        leftrightpulse=500
    robot.Servo_control(leftrightpulse, updownpulse)

def camservoInitFunction():
    global leftrightpulse, updownpulse
    leftrightpulse = 1500
    updownpulse = 1500
    robot.Servo_control(leftrightpulse, updownpulse)

#封装websocket发送函数
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

#websocket通信建立
def start_tcp_server(ip, port):
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
        # 将Sec-WebSocket-Key先进行sha1加密,转成二进制后在使用base64加密
        response_key = base64.b64encode(hashlib.sha1(bytes(Sec_WebSocket_Key, encoding="utf8")).digest())
        response_key_str = str(response_key)
        response_key_str = response_key_str[2:30]
        # 构建websocket返回数据
        response = HANDSHAKE_STRING.replace("{1}", response_key_str).replace("{2}", ip + ":" + str(port))
        conn.send(response.encode())
        #手机已连接
        pygame.mixer.init()
        pygame.mixer.music.load('/home/pi/yahboom-raspblock/connect.mp3')
        pygame.mixer.music.play()
        handleTid = threading.Thread(target = message_handle, args = [conn])
        handleTid.setDaemon(True)
        handleTid.start()
    closeTid = threading.Thread(target = waitClose, args = [conn])
    closeTid.setDaemon(True)
    closeTid.start()

#关闭socket
def waitClose(sock):
    time.sleep(10)
    sock.close()

#解包数据
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
            decoded = info[6:]
 
        bytes_list = bytearray()
        for i in range(len(decoded)):
            chunk = decoded[i] ^ mask[i % 4]
            bytes_list.append(chunk)
        
        try:
            body = bytes_list.decode('utf-8')
        except UnicodeDecodeError:
            print('UnicodeDecodeError')
        gotdata=body 

        #此处解析数据协议
        dispatch(client,body)
            
        # body=body+'just_decode'
        # try:
        #     send_msg(client,body.encode('utf-8'))
        # except UnicodeDecodeError:
        #     print('UnicodeDecodeError')

#解析数据协议
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

    cmd_function = cmd[1:3]
    #全向轮运动协议
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
    #左右转向
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
    #摄像头运动控制
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
    #颜色+人脸 追踪
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
                    g_target_mode = 'color_track'
                    color_lower = np.array([0,43,46])
                    color_upper = np.array([10, 255, 255])
                    target_valuex = target_valuey = 1500
                    robot.Servo_control(1500,1500)
                elif target_select == '2':       #绿
                    g_mode = 'target_track'
                    color_lower = np.array([35,43,46])
                    color_upper = np.array([77, 255, 255])
                    target_valuex = target_valuey = 1500
                    robot.Servo_control(1500,1500)
                elif target_select == '3':       #蓝
                    g_mode='target_track'
                    color_lower = np.array([100,43,46])
                    color_upper = np.array([124, 255, 255])
                    target_valuex = target_valuey = 1500
                    robot.Servo_control(1500,1500)
                elif target_select == '4':       #黄
                    g_mode='target_track'
                    color_lower = np.array([26,43,46])
                    color_upper = np.array([34, 255, 255])
                    target_valuex = target_valuey = 1500
                    robot.Servo_control(1500,1500)
                elif target_select == '5':       #橙
                    g_mode=='target_track'
                    color_lower = np.array([11,43,46])
                    color_upper = np.array([25, 255, 255])
                    target_valuex = target_valuey = 1500
                    robot.Servo_control(1500,1500)
                elif target_select == '6':       #无
                    g_target_mode = '0'
                    color_lower = np.array([156,43,46])
                    color_upper = np.array([180, 255, 255])
                    target_valuex = target_valuey = 1500
                    robot.Servo_control(1500,1500)
                elif target_select == '7':      #人脸追踪
                    g_target_mode = 'face_track'
            else:
                print("cmd-04 expression parse failure!")
        except:
            print('cmd-04 parse failure!')
            pass
    #语音播报
    elif cmd_function == '05':
        if cmd[-1] == '#' and cmd[0:4] == '$05,':
            Voice_text = cmd[4:-1]
            if Voice_text != '':
                print('Voice_txt: %s'%Voice_text)
                result = client.synthesis(text = Voice_text, 
                                options={'spd':3,'vol':9,'per':2,})
                #将合成的语音写入文件
                if not isinstance(result,dict):
                    with open('audio.mp3','wb') as f:
                        f.write(result)
                        #我们利用树莓派自带的pygame
                        pygame.mixer.init()
                        pygame.mixer.music.load('/home/pi/yahboom-raspblock/audio.mp3')
                        pygame.mixer.music.play()
                else:
                    print(result)
        else:
            print("cmd-05 expression parse failure!")
    #标签识别
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
    #运动模式演示模式选择
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
    #麦克纳姆轮单独控制
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
    #麦克纳姆轮整体控制
    elif cmd_function == '09':
        reg = re.compile('^\$09,(?P<WheelA_speed>[^ ]*),(?P<WheelB_speed>[^ ]*),(?P<WheelC_speed>[^ ]*),(?P<WheelD_speed>[^ ]*)#')
        regMatch = reg.match(cmd)                        
        try:
            if (regMatch != None):
                linebits = regMatch.groupdict()
                Speed_WheelD = int(linebits['WheelA_speed'])
                Speed_WheelC = int(linebits['WheelB_speed'])
                Speed_WheelA = int(linebits['WheelC_speed'])
                Speed_WheelB = int(linebits['WheelD_speed'])

            else:
                print("cmd-09 expression parse failure!")
        except:
            print('cmd-09 parse failure!')
            pass
    #蜂鸣器控制
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
    #自动驾驶控制
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
                    robot.Servo_control(target_valuex,target_valuey)
                elif Auto_drive_state == '1':
                    g_auto_drive_switch = 'open'
                    target_valuex = 1550
                    target_valuey = 2060  #刘森调试  2000  2100 
                    robot.Servo_control(target_valuex,target_valuey)
            else:
                print("cmd-11 expression parse failure!")
        except:
            print('cmd-11 parse failure!')
            pass
    #遥控最大速度值设定
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
    #位置模式位移设置
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
    #功能界面模式选择
    elif cmd_function == '14':
        reg = re.compile('^\$14,(?P<mode_select>[^ ]*)#')
        regMatch = reg.match(cmd)                        
        try:
            if (regMatch != None):
                linebits = regMatch.groupdict()
                mode_select = linebits['mode_select']
                if mode_select == '0':
                    g_mode = '0'
                    #清除零界状态
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
    #遥控运动模式选择
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
    #Meanshift移动追踪参数设置
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
    #自动驾驶视野切换
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
        
# 打开串口
ser = serial.Serial("/dev/ttyAMA0", 115200)
ser.flushInput()
def Attitude_update():
    # 获得接收缓冲区字符
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
    # 清空接收缓冲区
    ser.flushInput()

#运动状态刷新进程
def motion_refresh():
    global Speed_axis_X,Speed_axis_Y,Speed_axis_Z
    global Speed_WheelA, Speed_WheelB, Speed_WheelC, Speed_WheelD
    global Position_disp_X, Position_disp_Y, Position_disp_Z
    global Max_speed_XY, Max_speed_Z
    global g_servormode, g_mode, g_robot_motion_mode, g_z_state, g_presentation_mode, g_Position_update
    #小车运动模式
    #0 -> 速度模式 | 1 -> 位置模式
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
                camUpFunction()
            elif g_servormode == 'servo_down':
                camDownFunction()
            elif g_servormode == 'servo_left':
                camLeftFunction()
            elif g_servormode == 'servo_right':
                camRightFunction()
            elif g_servormode=='servo_init':
                g_servormode = '0'
                camservoInitFunction()
        elif g_mode == 'presentation':
            if g_presentation_mode == 'around':
                pass
            if g_presentation_mode == 'translation':
                pass
            if g_presentation_mode == 'stabilize':
                robot.Speed_axis_Yawhold_control(0, 0)
            if g_presentation_mode == 'position':
                if g_Position_update == 1:
                    robot.Position_disp_control(Position_disp_X, Position_disp_Y, Position_disp_Z)
                    g_Position_update = 0
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

#Tensorflow AI对象识别初始化
# Init tf model
MODEL_NAME = 'ssdlite_mobilenet_v2_coco_2018_05_09' #fast
PATH_TO_CKPT = MODEL_NAME + '/frozen_inference_graph.pb' 
PATH_TO_LABELS = os.path.join('data', 'mscoco_label_map.pbtxt') 
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

#Tensorflow AI对象识别初始化结束

###对信号(signal)进行均值滤波，滤波窗口大小为 window_size
###要求信号(signal)是一个列表(list)
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
    for i in range(1, length_data - 1): # 在整个 B 的长度内找出极值
        if (filtered_signal[i - 1] < filtered_signal[i] and filtered_signal[i] > filtered_signal[i + 1]
    and filtered_signal[i] > thre): # 找出极值，并设置阈值，这里阈值设为 20
            l.append(i) # 找出极值的位置
        elif (filtered_signal[i] == filtered_signal[i - 1] and filtered_signal[i] > thre):
            l.append(i) # 最高点前后可能有相等的情况
    CC = len(l) # 统计极值有几个，如果有两条线，就会有两个，如果有一条线就只有一个
    cou = 0
    for j in range(1, CC):
        if l[j] - l[j - 1] < peak_width: # 此判断用于将位于同一个峰内的极值点去除
            cou = cou + 1
    rcou = CC - cou
    return rcou


# 根据状态机来运行程序包含视频流返回
def mode_handle():
    global color_lower, color_upper
    global g_tag_identify_switch, g_tag_brodcast_switch
    global g_mode, g_socket, g_target_mode, g_tag_select
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
    thre = 1300 #峰的阈值高度，只有高于此值才算一个峰，否则算是噪声波动，建议这个值在均值之上
    peak_width =20 #为了避免一个峰内出现几个尖峰而导致被判别为多个峰，这里设定峰的宽度，在此宽度内均认为属于同一个峰
    
    matSrc = np.float32([[0, 149],  [310, 149], [271, 72], [43, 72]])
    matDst = np.float32([[100,240], [200,240], [200,0], [100,0]])
    #matDst = np.float32([[0,149], [310,149], [310,72], [0,72]])
    
    matAffine = cv2.getPerspectiveTransform(matSrc,matDst)# mat 1 src 2 dst
     #src 4->dst 4 (左下角 右下角 右上角 左上角 )
    pts = np.array([[0, 149],  [310, 149], [271, 72], [43, 72]], np.int32)


    g_camera = cv2.VideoCapture(0)
    g_camera.set(3, 320)
    g_camera.set(4, 240)
    g_camera.set(5, 120)  #设置帧率
    g_camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))
    g_camera.set(cv2.CAP_PROP_BRIGHTNESS, 40) #设置亮度 -64 - 64  0.0
    g_camera.set(cv2.CAP_PROP_CONTRAST, 50) #设置对比度 -64 - 64  2.0
    g_camera.set(cv2.CAP_PROP_EXPOSURE, 156) #设置曝光值 1.0 - 5000  156.0
    retval, frame = g_camera.read()
    imgencode = cv2.imencode('.jpg', frame)[1]

    xservo_pid = PID.PositionalPID(1.1, 0.2, 0.8)
    yservo_pid = PID.PositionalPID(0.8, 0.2, 0.8)
    #自动驾驶转向角PID
    Z_axis_pid = PID.PositionalPID(1.2, 0, 0.1)
    
    #人脸识别分类器文件
    face_haar = cv2.CascadeClassifier("haarcascade_profileface.xml")
    
    #物体识别session
    sess =  tf.compat.v1.Session(graph=detection_graph)
    
    camservoInitFunction()

    # 开机运行的Meanshift初始化
    retval, frame = g_camera.read()
    # 设置窗口的初始位置
    track_window = (meanshift_X, meanshift_Y, meanshift_width, meanshift_high)
    # 建立跟踪的ROI 
    roi = frame[meanshift_Y:meanshift_Y+meanshift_high, meanshift_X:meanshift_X+meanshift_width]
    # frame = cv2.rectangle(frame, (140,100), (180,140), 255,2)
    #图片从RGB空间转换为HSV空间
    hsv_roi = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    #将低亮度的值忽略掉 
    mask = cv2.inRange(hsv_roi, np.array((0., 60.,32.)), np.array((180.,255.,255.)))
    #计算图像直方图
    roi_hist = cv2.calcHist([hsv_roi],[0],mask,[180],[0,180])
    #归一化处理
    cv2.normalize(roi_hist,roi_hist,0,255,cv2.NORM_MINMAX)
    # 设置终止标准，10次迭代或至少移动1 pt
    term_crit = ( cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1 )
    robot.BoardData_Get(0)  #使能自动上报数据
    
    while 1:
        if g_mode == 'auto_drive':
            if g_camera.get(cv2.CAP_PROP_FRAME_WIDTH) != 1920:
                g_camera.release()
                g_camera = cv2.VideoCapture(0)
                g_camera.set(3, 1920)
                g_camera.set(4, 1080)
                g_camera.set(5, 30)  #设置帧率
                g_camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))
                g_camera.set(cv2.CAP_PROP_BRIGHTNESS, 40) #设置亮度 -64 - 64  0.0
                g_camera.set(cv2.CAP_PROP_CONTRAST, 50) #设置对比度 -64 - 64  2.0
                g_camera.set(cv2.CAP_PROP_EXPOSURE, 156)  #设置曝光值 1.0 - 5000  156.0
        else:
            if g_camera.get(cv2.CAP_PROP_FRAME_WIDTH) != 320:
                g_camera.release()
                g_camera = cv2.VideoCapture(0)
                g_camera.set(3, 640)
                g_camera.set(4, 480)
                g_camera.set(5, 120)  #设置帧率
                g_camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))
                g_camera.set(cv2.CAP_PROP_BRIGHTNESS, 40) #设置亮度 -64 - 64  0.0
                g_camera.set(cv2.CAP_PROP_CONTRAST, 50) #设置对比度 -64 - 64  2.0
                g_camera.set(cv2.CAP_PROP_EXPOSURE, 156)  #设置曝光值 1.0 - 5000  156.0
        
        retval, frame = g_camera.read()
        if retval == False:  #防止未读取正确视频图像
            print('read camera err!')
            continue
        #############
        fps = fps + 1
        mfps = fps / (time.time() - t_start)
        #cv2.putText(img, str(i), (123,456)), font, 2, (0,255,0), 3) 
        #各参数依次是：图片，添加的文字，左上角坐标，字体，字体大小，颜色，字体粗细
        if g_mode == 'target_track':
            if g_target_mode == 'face_track':
                # 把图像转为黑白图像
                gray_img = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_haar.detectMultiScale(gray_img, 1.1, 3)
                if len(faces)>0:
                    (face_x, face_y, face_w, face_h) = faces[0]
                    # cv2.rectangle(frame,(face_x+10,face_y),(face_x+face_w-10,face_y+face_h+20),(0,255,0),2)
                    cv2.rectangle(frame,(face_x,face_y),(face_x+face_w,face_y+face_h),(0,255,0),2)

                    #Proportion-Integration-Differentiation算法
                    # 输入X轴方向参数PID控制输入
                    xservo_pid.SystemOutput = face_x+face_w/2
                    xservo_pid.SetStepSignal(150)
                    xservo_pid.SetInertiaTime(0.01, 0.1)
                    target_valuex = int(1500 + xservo_pid.SystemOutput)
                    # 输入Y轴方向参数PID控制输入
                    yservo_pid.SystemOutput = face_y+face_h/2
                    yservo_pid.SetStepSignal(120)
                    yservo_pid.SetInertiaTime(0.01, 0.1)
                    target_valuey = int(1500 - yservo_pid.SystemOutput)
                    # 将云台转动至PID调校位置
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
                        # 将检测到的颜色标记出来
                        cv2.circle(frame,(int(color_x),int(color_y)),int(color_radius),(255,0,255),2)  
                        #Proportion-Integration-Differentiation
                        xservo_pid.SystemOutput = color_x
                        xservo_pid.SetStepSignal(150)
                        xservo_pid.SetInertiaTime(0.01, 0.1)
                        target_valuex = int(1500+xservo_pid.SystemOutput)
                        # 输入Y轴方向参数PID控制输入
                        yservo_pid.SystemOutput = color_y
                        yservo_pid.SetStepSignal(150)
                        yservo_pid.SetInertiaTime(0.01, 0.1)
                        target_valuey = int(1500-yservo_pid.SystemOutput)
                        # 将云台转动至PID调校位置
                        robot.Servo_control(target_valuex,target_valuey)
            elif g_target_mode == 'meanshift_track':
                if meanshift_update_flag == 1:
                    print('Meanshift init!')
                    # 设置窗口的初始位置
                    track_window = (meanshift_X, meanshift_Y, meanshift_width, meanshift_high)
                    # 建立跟踪的ROI 
                    roi = frame[meanshift_Y:meanshift_Y+meanshift_high, meanshift_X:meanshift_X+meanshift_width]
                    frame = cv2.rectangle(frame, (140,100), (180,140), 255,2)
                    #图片从RGB空间转换为HSV空间
                    hsv_roi = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                    #将低亮度的值忽略掉 
                    mask = cv2.inRange(hsv_roi, np.array((0., 60.,32.)), np.array((180.,255.,255.)))
                    #计算图像直方图
                    roi_hist = cv2.calcHist([hsv_roi],[0],mask,[180],[0,180])
                    #归一化处理
                    cv2.normalize(roi_hist,roi_hist,0,255,cv2.NORM_MINMAX)
                    # 设置终止标准，10次迭代或至少移动1 pt
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
                        # 提取二维码的边界框的位置
                        # 画出图像中条形码的边界框
                        (x, y, w, h) = barcode.rect
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (225, 225, 225), 2)
                        # 提取二维码数据为字节对象，所以如果我们想在输出图像上
                        # 画出来，就需要先将它转换成字符串
                        barcodeData = barcode.data.decode("utf-8")
                        barcodeType = barcode.type
                        # 绘出图像上条形码的数据和条形码类型
                        text = "{} ({})".format(barcodeData, barcodeType)
                        cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,0.5, (225, 225, 225), 2)
                        # 向终端打印条形码数据和条形码类型
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
                if g_tag_brodcast_switch == 'open':
                    if identify_tag != '':
                        if identify_tag != last_identify_tag:
                            if g_tag_select == 'object':
                                object_brodcast_delay += 1
                                if object_brodcast_delay >= 8:
                                    result = client.synthesis(text = identify_tag, 
                                    options={'spd':3,'vol':9,'per':2,})
                                    #将合成的语音写进文件
                                    if not isinstance(result,dict):
                                        with open('audio.mp3','wb') as f:
                                            f.write(result)
                                            #我们利用树莓派自带的pygame
                                            pygame.mixer.init()
                                            pygame.mixer.music.load('/home/pi/yahboom-raspblock/audio.mp3')
                                            pygame.mixer.music.play()
                                            last_identify_tag = identify_tag
                                    else:
                                        print(result)
                                    object_brodcast_delay = 0
                            elif g_tag_select == 'qrcode':
                                result = client.synthesis(text = identify_tag, 
                                    options={'spd':3,'vol':9,'per':2,})
                                #将合成的语音写进文件
                                if not isinstance(result,dict):
                                    with open('audio.mp3','wb') as f:
                                        f.write(result)
                                        #我们利用树莓派自带的pygame
                                        pygame.mixer.init()
                                        pygame.mixer.music.load('/home/pi/yahboom-raspblock/audio.mp3')
                                        pygame.mixer.music.play()
                                        last_identify_tag = identify_tag
                                else:
                                    print(result)
        elif g_mode == 'auto_drive':
            frame = cv2.resize(frame,(320,240))
            dst = cv2.warpPerspective(frame,matAffine,(320,240))
            # 顶点个数：4，矩阵变成4*1*2维
            # OpenCV中需要将多边形的顶点坐标变成顶点数×1×2维的矩阵
            # 这里 reshape 的第一个参数为-1, 表示“任意”，意思是这一维的值是根据后面的维度的计算出来的
            pts = pts.reshape((-1, 1, 2))
            cv2.polylines(frame, [pts],True, (255, 0, 0), 3)

            dst_gray = cv2.cvtColor(dst, cv2.COLOR_RGB2GRAY)
            dst_retval, dst_binaryzation = cv2.threshold(dst_gray, 100, 255, cv2.THRESH_BINARY)
            dst_binaryzation = cv2.erode(dst_binaryzation, None, iterations=1)
            histogram = np.sum(dst_binaryzation[dst_binaryzation.shape[0]//2:,:], axis=0)
            midpoint = np.int(histogram.shape[0]/2)
            leftx_base = np.argmax(histogram[:midpoint],axis = 0)
            rightx_base = np.argmax(histogram[midpoint:],axis = 0) + midpoint

            leftx_base_value = np.max(histogram[:midpoint],axis = 0)
            rightx_base_value = np.max(histogram[midpoint:],axis = 0)

            if leftx_base < 100:
                leftx_base = 100
            if rightx_base > 200:
                rightx_base = 200
            elif rightx_base == 160:
                rightx_base = 200

            histogram = np.sum(dst_binaryzation[dst_binaryzation.shape[0]//2:,:], axis=0)
            dst_binaryzation = cv2.cvtColor(dst_binaryzation,cv2.COLOR_GRAY2RGB)
            cv2.line(dst_binaryzation,(149,0),(149,240),(255,0,255),2)
            lane_center = int((leftx_base + rightx_base)/2)
            cv2.line(dst_binaryzation,(leftx_base,0),(leftx_base,240),(0,255,0),2)
            cv2.line(dst_binaryzation,(rightx_base,0),(rightx_base,240),(0,255,0),2)
            cv2.line(dst_binaryzation,(lane_center,0),(lane_center,240),(255,0,0),2)
            Bias = 149 - lane_center
            

            if(Bias > 20):
                Bias = 20
            elif Bias < -20:
                Bias = -20
                
            #转向角PID调节
            Z_axis_pid.SystemOutput = Bias
            Z_axis_pid.SetStepSignal(0)
            Z_axis_pid.SetInertiaTime(0.5, 0.2)

            if Z_axis_pid.SystemOutput > 20:
                Z_axis_pid.SystemOutput = 20
            elif Z_axis_pid.SystemOutput < -20:
                Z_axis_pid.SystemOutput = -20

            filtered_signal = mean_filter(histogram, window_size)
            length_data = len(filtered_signal)
            peaks_count = find_peak(filtered_signal, length_data, thre, peak_width)
            
            if g_auto_drive_switch == 'open':
                if peaks_count == 2 or peaks_count == 4:
                    robot.Speed_axis_control(0,5,int(Z_axis_pid.SystemOutput)+3)
                elif peaks_count == 1:
                    if leftx_base_value == 0 or (rightx_base_value > leftx_base_value):
                        # robot.Speed_axis_control(0,5,abs(int(Z_axis_pid.SystemOutput))+3,0,0,0)
                        robot.Speed_axis_control(0,5,-12)
                    elif rightx_base_value == 0 or (leftx_base_value > rightx_base_value):
                        # robot.Speed_axis_control(0,5,int(Z_axis_pid.SystemOutput)+3,0,0,1)
                        robot.Speed_axis_control(0,5,12)
                    else:
                        robot.Speed_axis_control(0,5,-12)
                elif peaks_count == 3:
                    robot.Speed_axis_control(0, 5, 0)
            if g_drive_view_switch == 0:
                cv2.putText(frame, "FPS:  " + str(int(mfps)), (10, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                imgencode = cv2.imencode('.jpg', frame)[1]
            elif g_drive_view_switch == 1:
                cv2.putText(dst, "FPS:  " + str(int(mfps)), (10, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                imgencode = cv2.imencode('.jpg', dst)[1]
            elif g_drive_view_switch == 2:
                cv2.putText(dst_binaryzation, "FPS:  " + str(int(mfps)), (10,15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255), 2)
                cv2.putText(dst_binaryzation, "Bias: " + str(int(Bias)), (10,35), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255), 2)
                cv2.putText(dst_binaryzation, "Peaks: " + str(int(peaks_count)), (10,55), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255), 2)
                cv2.putText(dst_binaryzation, "L_peak: " + str(int(leftx_base_value)), (10,75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255), 2)
                cv2.putText(dst_binaryzation, "R_peak: " + str(int(rightx_base_value)), (10, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
                imgencode = cv2.imencode('.jpg', dst_binaryzation)[1]

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
    robot.BoardData_Get(9)  #关闭自动上报数据
        
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

    app.run(host='0.0.0.0', port=6001, debug=False)
    