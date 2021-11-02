# uncompyle6 version 3.8.0
# Python bytecode 3.7.0 (3394)
# Decompiled from: Python 3.7.3 (default, Jul 25 2020, 13:03:44) 
# [GCC 8.3.0]
# Embedded file name: Yahboom_Raspblock_1.py
# Compiled at: 2020-08-07 17:38:38
# Size of source mod 2**32: 72529 bytes
"""
@Copyright (C): 2010-2022, Shenzhen Yahboom Tech
@Author: Malloy.Yuan
@Date: 2019-08-02 12:03:42
@LastEditors  : Liusen
@LastEditTime : 2020-03-23 16:15:03
"""
from flask import Flask, render_template, Response
from importlib import import_module
import os, serial, socket, base64, hashlib, sys, struct, threading, hashlib, re, time, cv2, PID, pygame, numpy as np
from Raspblock import Raspblock
from aip import AipSpeech
import pyzbar.pyzbar as pyzbar
from PIL import Image, ImageDraw, ImageFont
import tensorflow as tf
from object_detection.utils import label_map_util
import object_detection.utils as vis_utils
import demjson
from aip import AipBodyAnalysis
hand = {'One':'one', 
 'Five':'five',  'Fist':'fist',  'Ok':'OK',  'Prayer':'pray', 
 'Congratulation':'congratulation',  'Honour':'honour',  'Heart_single':'heart_single', 
 'Thumb_up':'thumb_up',  'Thumb_down':'thumb_down',  'ILY':'i_love_you', 
 'Palm_up':'palm_up',  'Heart_1':'Heart_one',  'Heart_2':'Heart_tow', 
 'Heart_3':'Heart_three',  'Two':'two',  'Three':'three', 
 'Four':'four',  'Six':'six',  'Seven':'seven',  'Eight':'eight', 
 'Nine':'nine',  'Rock':'Rock',  'Face':'face'}
APP_ID_Body = '18550528'
API_KEY_Body = 'K6PWqtiUTKYK1fYaz13O8E3i'
SECRET_KEY_Body = 'IDBUII1j6srF1XVNDX32I2WpuwBWczzK'
client_body = AipBodyAnalysis(APP_ID_Body, API_KEY_Body, SECRET_KEY_Body)
APP_ID = '17852430'
API_KEY = 'eGeO4iQGAjHCrzBTYd1uvTtf'
SECRET_KEY = 'Cn1EVsUngZDbRLv4OxAFrDHSo8PsvFVP'
client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)
import logging
from logging import handlers

class Logger(object):
    level_relations = {'debug':logging.DEBUG, 
     'info':logging.INFO, 
     'warning':logging.WARNING, 
     'error':logging.ERROR, 
     'crit':logging.CRITICAL}

    def __init__(self, filename, level='info', when='D', backCount=3, fmt='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'):
        self.logger = logging.getLogger(filename)
        format_str = logging.Formatter(fmt)
        self.logger.setLevel(self.level_relations.get(level))
        sh = logging.StreamHandler()
        sh.setFormatter(format_str)
        th = handlers.TimedRotatingFileHandler(filename=filename, when=when, backupCount=backCount, encoding='utf-8')
        th.setFormatter(format_str)
        self.logger.addHandler(sh)
        self.logger.addHandler(th)


g_mode = '0'
g_servormode = '0'
g_robot_motion_mode = 'Free'
g_z_state = 'unlock'
g_presentation_mode = '0'
g_Position_update = 0
g_target_mode = '0'
g_tag_select = 'qrcode'
g_tag_identify_switch = 'close'
g_tag_brodcast_switch = 'close'
g_auto_drive_switch = 'close'
g_drive_view_switch = 0
Speed_axis_X = 0
Speed_axis_Y = 0
Speed_axis_Z = 0
Speed_WheelA = 0
Speed_WheelB = 0
Speed_WheelC = 0
Speed_WheelD = 0
Position_disp_X = 0
Position_disp_Y = 0
Position_disp_Z = 0
Max_speed_XY = 12
Max_speed_Z = 12
meanshift_X = 0
meanshift_Y = 0
meanshift_width = 40
meanshift_high = 40
meanshift_update_flag = 0
g_init = False
leftrightpulse = 1500
updownpulse = 1500
color_lower = np.array([156, 43, 46])
color_upper = np.array([180, 255, 255])
target_valuex = 1500
target_valuey = 1500
robot = Raspblock()
HANDSHAKE_STRING = 'HTTP/1.1 101 Switching Protocols\r\nUpgrade:websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: {1}\r\nWebSocket-Location: ws://{2}/chat\r\nWebSocket-Protocol:chat\r\n\r\n'
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    return Response((mode_handle()), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/init')
def init():
    global g_init
    if g_init == False:
        tid = threading.Thread(target=start_tcp_server, args=(6000, ))
        tid.setDaemon(True)
        tid.start()
    print('init websocket!!!!!!!!!')
    return render_template('init.html')


def camUpFunction(num):
    global leftrightpulse
    global updownpulse
    updownpulse -= num
    if updownpulse > 2500:
        updownpulse = 2500
    robot.Servo_control(leftrightpulse, updownpulse)


def camDownFunction(num):
    global updownpulse
    updownpulse += num
    if updownpulse < 500:
        updownpulse = 500
    robot.Servo_control(leftrightpulse, updownpulse)


def camLeftFunction(num):
    global leftrightpulse
    leftrightpulse += num
    if leftrightpulse > 2500:
        leftrightpulse = 2500
    robot.Servo_control(leftrightpulse, updownpulse)


def camRightFunction(num):
    global leftrightpulse
    leftrightpulse -= num
    if leftrightpulse < 500:
        leftrightpulse = 500
    robot.Servo_control(leftrightpulse, updownpulse)


def camservoInitFunction():
    global leftrightpulse
    global updownpulse
    leftrightpulse = 1500
    updownpulse = 1500
    robot.Servo_control(leftrightpulse, updownpulse)


def cv2ImgAddText(img, text, left, top, textColor=(0, 255, 0), textSize=20):
    if isinstance(img, np.ndarray):
        img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img)
    fontStyle = ImageFont.truetype('/home/pi/yahboom-raspblock/simhei.ttf',
      textSize, encoding='utf-8')
    draw.text((left, top), text, textColor, font=fontStyle)
    return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)


def send_msg(conn, msg_bytes):
    import struct
    token = b'\x81'
    length = len(msg_bytes)
    if length < 126:
        token += struct.pack('B', length)
    else:
        if length <= 65535:
            token += struct.pack('!BH', 126, length)
        else:
            token += struct.pack('!BQ', 127, length)
    msg = token + msg_bytes
    conn.send(msg)
    return True


def getip():
    try:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('www.baidu.com', 0))
            ip = s.getsockname()[0]
        except:
            ip = 'x.x.x.x'

    finally:
        s.close()

    return ip


def start_tcp_server(port):
    global g_init
    global g_socket
    g_init = True
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ip = getip()
    while ip == 'x.x.x.x':
        time.sleep(5)

    sock.bind((ip, port))
    sock.listen(5)
    while True:
        conn, address = sock.accept()
        g_socket = conn
        request = conn.recv(2048)
        print(request.decode())
        ret = re.search('Sec-WebSocket-Key: (.*==)', str(request.decode()))
        if ret:
            key = ret.group(1)
        else:
            return
            Sec_WebSocket_Key = key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
            response_key = base64.b64encode(hashlib.sha1(bytes(Sec_WebSocket_Key, encoding='utf8')).digest())
            response_key_str = str(response_key)
            response_key_str = response_key_str[2:30]
            response = HANDSHAKE_STRING.replace('{1}', response_key_str).replace('{2}', ip + ':' + str(port))
            conn.send(response.encode())
            pygame.mixer.init()
            pygame.mixer.music.load('/home/pi/yahboom-raspblock/connect.mp3')
            pygame.mixer.music.play()
            handleTid = threading.Thread(target=message_handle, args=[conn])
            handleTid.setDaemon(True)
            handleTid.start()

    closeTid = threading.Thread(target=waitClose, args=[conn])
    closeTid.setDaemon(True)
    closeTid.start()


def waitClose(sock):
    time.sleep(10)
    sock.close()


def message_handle(client):
    lastCmd = ''
    while True:
        try:
            info = client.recv(8096)
        except Exception as e:
            try:
                info = None
            finally:
                e = None
                del e

        if not info:
            print('break thread')
            break
        else:
            payload_len = info[1] & 127
            print(payload_len)
            if payload_len == 126:
                extend_payload_len = info[2:4]
                mask = info[4:8]
                decoded = info[8:]
            else:
                if payload_len == 127:
                    extend_payload_len = info[2:10]
                    mask = info[10:14]
                    decoded = info[14:]
                else:
                    extend_payload_len = None
                    mask = info[2:6]
                    decoded = info[6:payload_len + 6]
        bytes_list = bytearray()
        for i in range(len(decoded)):
            chunk = decoded[i] ^ mask[(i % 4)]
            bytes_list.append(chunk)

        try:
            body = str(bytes_list, encoding='utf-8')
        except UnicodeDecodeError:
            body = '$01,X0.00Y0.00#'
            print(bytes_list)
            print('UnicodeDecodeError')

        gotdata = body
        print(body)
        dispatch(client, body)


def dispatch--- This code section failed: ---

 L. 430         0  LOAD_FAST                'cmd'
                2  LOAD_CONST               1
                4  LOAD_CONST               3
                6  BUILD_SLICE_2         2 
                8  BINARY_SUBSCR    
               10  STORE_FAST               'cmd_function'

 L. 432        12  LOAD_FAST                'cmd_function'
               14  LOAD_STR                 '01'
               16  COMPARE_OP               ==
               18  POP_JUMP_IF_FALSE   138  'to 138'

 L. 433        20  LOAD_GLOBAL              re
               22  LOAD_METHOD              compile
               24  LOAD_STR                 '^\\$01,X(?P<Speed_axis_X>[^ ]*)Y(?P<Speed_axis_Y>[^ ]*)#'
               26  CALL_METHOD_1         1  '1 positional argument'
               28  STORE_FAST               'reg'

 L. 434        30  LOAD_FAST                'reg'
               32  LOAD_METHOD              match
               34  LOAD_FAST                'cmd'
               36  CALL_METHOD_1         1  '1 positional argument'
               38  STORE_FAST               'regMatch'

 L. 435        40  SETUP_EXCEPT        114  'to 114'

 L. 436        42  LOAD_FAST                'regMatch'
               44  LOAD_CONST               None
               46  COMPARE_OP               !=
               48  POP_JUMP_IF_FALSE   102  'to 102'

 L. 437        50  LOAD_FAST                'regMatch'
               52  LOAD_METHOD              groupdict
               54  CALL_METHOD_0         0  '0 positional arguments'
               56  STORE_FAST               'linebits'

 L. 438        58  LOAD_GLOBAL              int
               60  LOAD_GLOBAL              float
               62  LOAD_FAST                'linebits'
               64  LOAD_STR                 'Speed_axis_X'
               66  BINARY_SUBSCR    
               68  CALL_FUNCTION_1       1  '1 positional argument'
               70  LOAD_GLOBAL              Max_speed_XY
               72  BINARY_MULTIPLY  
               74  CALL_FUNCTION_1       1  '1 positional argument'
               76  STORE_GLOBAL             Speed_axis_X

 L. 439        78  LOAD_GLOBAL              int
               80  LOAD_GLOBAL              float
               82  LOAD_FAST                'linebits'
               84  LOAD_STR                 'Speed_axis_Y'
               86  BINARY_SUBSCR    
               88  CALL_FUNCTION_1       1  '1 positional argument'
               90  LOAD_GLOBAL              Max_speed_XY
               92  BINARY_MULTIPLY  
               94  CALL_FUNCTION_1       1  '1 positional argument'
               96  UNARY_NEGATIVE   
               98  STORE_GLOBAL             Speed_axis_Y
              100  JUMP_FORWARD        110  'to 110'
            102_0  COME_FROM            48  '48'

 L. 441       102  LOAD_GLOBAL              print
              104  LOAD_STR                 'cmd-01 expression parse failure!'
              106  CALL_FUNCTION_1       1  '1 positional argument'
              108  POP_TOP          
            110_0  COME_FROM           100  '100'
              110  POP_BLOCK        
              112  JUMP_FORWARD       3526  'to 3526'
            114_0  COME_FROM_EXCEPT     40  '40'

 L. 442       114  POP_TOP          
              116  POP_TOP          
              118  POP_TOP          

 L. 443       120  LOAD_GLOBAL              print
              122  LOAD_STR                 'cmd-01 parse failure!'
              124  CALL_FUNCTION_1       1  '1 positional argument'
              126  POP_TOP          

 L. 444       128  POP_EXCEPT       
              130  JUMP_FORWARD       3526  'to 3526'
              132  END_FINALLY      
          134_136  JUMP_FORWARD       3526  'to 3526'
            138_0  COME_FROM            18  '18'

 L. 446       138  LOAD_FAST                'cmd_function'
              140  LOAD_STR                 '02'
              142  COMPARE_OP               ==
          144_146  POP_JUMP_IF_FALSE   286  'to 286'

 L. 447       148  LOAD_GLOBAL              re
              150  LOAD_METHOD              compile
              152  LOAD_STR                 '^\\$02,(?P<Turn_action>[^ ]*)#'
              154  CALL_METHOD_1         1  '1 positional argument'
              156  STORE_FAST               'reg'

 L. 448       158  LOAD_FAST                'reg'
              160  LOAD_METHOD              match
              162  LOAD_FAST                'cmd'
              164  CALL_METHOD_1         1  '1 positional argument'
              166  STORE_FAST               'regMatch'

 L. 449       168  SETUP_EXCEPT        262  'to 262'

 L. 450       170  LOAD_FAST                'regMatch'
              172  LOAD_CONST               None
              174  COMPARE_OP               !=
              176  POP_JUMP_IF_FALSE   250  'to 250'

 L. 451       178  LOAD_FAST                'regMatch'
              180  LOAD_METHOD              groupdict
              182  CALL_METHOD_0         0  '0 positional arguments'
              184  STORE_FAST               'linebits'

 L. 452       186  LOAD_FAST                'linebits'
              188  LOAD_STR                 'Turn_action'
              190  BINARY_SUBSCR    
              192  STORE_FAST               'Turn_action'

 L. 453       194  LOAD_FAST                'Turn_action'
              196  LOAD_STR                 '1'
              198  COMPARE_OP               ==
              200  POP_JUMP_IF_FALSE   214  'to 214'

 L. 454       202  LOAD_GLOBAL              Max_speed_Z
              204  UNARY_NEGATIVE   
              206  STORE_GLOBAL             Speed_axis_Z

 L. 455       208  LOAD_STR                 'unlock'
              210  STORE_GLOBAL             g_z_state
              212  JUMP_FORWARD        248  'to 248'
            214_0  COME_FROM           200  '200'

 L. 456       214  LOAD_FAST                'Turn_action'
              216  LOAD_STR                 '2'
              218  COMPARE_OP               ==
              220  POP_JUMP_IF_FALSE   232  'to 232'

 L. 457       222  LOAD_GLOBAL              Max_speed_Z
              224  STORE_GLOBAL             Speed_axis_Z

 L. 458       226  LOAD_STR                 'unlock'
              228  STORE_GLOBAL             g_z_state
              230  JUMP_FORWARD        248  'to 248'
            232_0  COME_FROM           220  '220'

 L. 459       232  LOAD_FAST                'Turn_action'
              234  LOAD_STR                 '3'
              236  COMPARE_OP               ==
              238  POP_JUMP_IF_FALSE   248  'to 248'

 L. 460       240  LOAD_CONST               0
              242  STORE_GLOBAL             Speed_axis_Z

 L. 461       244  LOAD_STR                 'lock'
              246  STORE_GLOBAL             g_z_state
            248_0  COME_FROM           238  '238'
            248_1  COME_FROM           230  '230'
            248_2  COME_FROM           212  '212'
              248  JUMP_FORWARD        258  'to 258'
            250_0  COME_FROM           176  '176'

 L. 463       250  LOAD_GLOBAL              print
              252  LOAD_STR                 'cmd-02 expression parse failure!'
              254  CALL_FUNCTION_1       1  '1 positional argument'
              256  POP_TOP          
            258_0  COME_FROM           248  '248'
              258  POP_BLOCK        
              260  JUMP_FORWARD       3526  'to 3526'
            262_0  COME_FROM_EXCEPT    168  '168'

 L. 464       262  POP_TOP          
              264  POP_TOP          
              266  POP_TOP          

 L. 465       268  LOAD_GLOBAL              print
              270  LOAD_STR                 'cmd-02 parse failure!'
              272  CALL_FUNCTION_1       1  '1 positional argument'
              274  POP_TOP          

 L. 466       276  POP_EXCEPT       
              278  JUMP_FORWARD       3526  'to 3526'
              280  END_FINALLY      
          282_284  JUMP_FORWARD       3526  'to 3526'
            286_0  COME_FROM           144  '144'

 L. 468       286  LOAD_FAST                'cmd_function'
              288  LOAD_STR                 '03'
              290  COMPARE_OP               ==
          292_294  POP_JUMP_IF_FALSE   476  'to 476'

 L. 469       296  LOAD_GLOBAL              re
              298  LOAD_METHOD              compile
              300  LOAD_STR                 '^\\$03,(?P<Servo_action>[^ ]*)#'
              302  CALL_METHOD_1         1  '1 positional argument'
              304  STORE_FAST               'reg'

 L. 470       306  LOAD_FAST                'reg'
              308  LOAD_METHOD              match
              310  LOAD_FAST                'cmd'
              312  CALL_METHOD_1         1  '1 positional argument'
              314  STORE_FAST               'regMatch'

 L. 471       316  SETUP_EXCEPT        452  'to 452'

 L. 472       318  LOAD_FAST                'regMatch'
              320  LOAD_CONST               None
              322  COMPARE_OP               !=
          324_326  POP_JUMP_IF_FALSE   440  'to 440'

 L. 473       328  LOAD_FAST                'regMatch'
              330  LOAD_METHOD              groupdict
              332  CALL_METHOD_0         0  '0 positional arguments'
              334  STORE_FAST               'linebits'

 L. 474       336  LOAD_FAST                'linebits'
              338  LOAD_STR                 'Servo_action'
              340  BINARY_SUBSCR    
              342  STORE_FAST               'Servo_action'

 L. 476       344  LOAD_FAST                'Servo_action'
              346  LOAD_STR                 '1'
              348  COMPARE_OP               ==
          350_352  POP_JUMP_IF_FALSE   360  'to 360'

 L. 477       354  LOAD_STR                 'servo_forward'
              356  STORE_GLOBAL             g_servormode
              358  JUMP_FORWARD        438  'to 438'
            360_0  COME_FROM           350  '350'

 L. 478       360  LOAD_FAST                'Servo_action'
              362  LOAD_STR                 '2'
              364  COMPARE_OP               ==
          366_368  POP_JUMP_IF_FALSE   376  'to 376'

 L. 479       370  LOAD_STR                 'servo_down'
              372  STORE_GLOBAL             g_servormode
              374  JUMP_FORWARD        438  'to 438'
            376_0  COME_FROM           366  '366'

 L. 480       376  LOAD_FAST                'Servo_action'
              378  LOAD_STR                 '3'
              380  COMPARE_OP               ==
          382_384  POP_JUMP_IF_FALSE   392  'to 392'

 L. 481       386  LOAD_STR                 'servo_left'
              388  STORE_GLOBAL             g_servormode
              390  JUMP_FORWARD        438  'to 438'
            392_0  COME_FROM           382  '382'

 L. 482       392  LOAD_FAST                'Servo_action'
              394  LOAD_STR                 '4'
              396  COMPARE_OP               ==
          398_400  POP_JUMP_IF_FALSE   408  'to 408'

 L. 483       402  LOAD_STR                 'servo_right'
              404  STORE_GLOBAL             g_servormode
              406  JUMP_FORWARD        438  'to 438'
            408_0  COME_FROM           398  '398'

 L. 484       408  LOAD_FAST                'Servo_action'
              410  LOAD_STR                 '5'
              412  COMPARE_OP               ==
          414_416  POP_JUMP_IF_FALSE   424  'to 424'

 L. 485       418  LOAD_STR                 '0'
              420  STORE_GLOBAL             g_servormode
              422  JUMP_FORWARD        438  'to 438'
            424_0  COME_FROM           414  '414'

 L. 486       424  LOAD_FAST                'Servo_action'
              426  LOAD_STR                 '6'
              428  COMPARE_OP               ==
          430_432  POP_JUMP_IF_FALSE   448  'to 448'

 L. 487       434  LOAD_STR                 'servo_init'
              436  STORE_GLOBAL             g_servormode
            438_0  COME_FROM           422  '422'
            438_1  COME_FROM           406  '406'
            438_2  COME_FROM           390  '390'
            438_3  COME_FROM           374  '374'
            438_4  COME_FROM           358  '358'
              438  JUMP_FORWARD        448  'to 448'
            440_0  COME_FROM           324  '324'

 L. 490       440  LOAD_GLOBAL              print
              442  LOAD_STR                 'cmd-03 expression parse failure!'
              444  CALL_FUNCTION_1       1  '1 positional argument'
              446  POP_TOP          
            448_0  COME_FROM           438  '438'
            448_1  COME_FROM           430  '430'
              448  POP_BLOCK        
              450  JUMP_FORWARD       3526  'to 3526'
            452_0  COME_FROM_EXCEPT    316  '316'

 L. 491       452  POP_TOP          
              454  POP_TOP          
              456  POP_TOP          

 L. 492       458  LOAD_GLOBAL              print
              460  LOAD_STR                 'cmd-03 parse failure!'
              462  CALL_FUNCTION_1       1  '1 positional argument'
              464  POP_TOP          

 L. 493       466  POP_EXCEPT       
              468  JUMP_FORWARD       3526  'to 3526'
              470  END_FINALLY      
          472_474  JUMP_FORWARD       3526  'to 3526'
            476_0  COME_FROM           292  '292'

 L. 495       476  LOAD_FAST                'cmd_function'
              478  LOAD_STR                 '04'
              480  COMPARE_OP               ==
          482_484  POP_JUMP_IF_FALSE  1062  'to 1062'

 L. 496       486  LOAD_GLOBAL              re
              488  LOAD_METHOD              compile
              490  LOAD_STR                 '^\\$04,(?P<target_select>[^ ]*)#'
              492  CALL_METHOD_1         1  '1 positional argument'
              494  STORE_FAST               'reg'

 L. 497       496  LOAD_FAST                'reg'
              498  LOAD_METHOD              match
              500  LOAD_FAST                'cmd'
              502  CALL_METHOD_1         1  '1 positional argument'
              504  STORE_FAST               'regMatch'

 L. 498   506_508  SETUP_EXCEPT       1038  'to 1038'

 L. 499       510  LOAD_FAST                'regMatch'
              512  LOAD_CONST               None
              514  COMPARE_OP               !=
          516_518  POP_JUMP_IF_FALSE  1026  'to 1026'

 L. 500       520  LOAD_FAST                'regMatch'
              522  LOAD_METHOD              groupdict
              524  CALL_METHOD_0         0  '0 positional arguments'
              526  STORE_FAST               'linebits'

 L. 501       528  LOAD_FAST                'linebits'
              530  LOAD_STR                 'target_select'
              532  BINARY_SUBSCR    
              534  STORE_FAST               'target_select'

 L. 502       536  LOAD_FAST                'target_select'
              538  LOAD_STR                 '0'
              540  COMPARE_OP               ==
          542_544  POP_JUMP_IF_FALSE   570  'to 570'

 L. 503       546  LOAD_STR                 '0'
              548  STORE_GLOBAL             g_target_mode

 L. 504       550  LOAD_CONST               1500
              552  DUP_TOP          
              554  STORE_FAST               'target_valuex'
              556  STORE_FAST               'target_valuey'

 L. 505       558  LOAD_GLOBAL              robot
              560  LOAD_METHOD              Servo_control
              562  LOAD_CONST               1500
              564  LOAD_CONST               1500
              566  CALL_METHOD_2         2  '2 positional arguments'
              568  POP_TOP          
            570_0  COME_FROM           542  '542'

 L. 506       570  LOAD_FAST                'target_select'
              572  LOAD_STR                 '1'
              574  COMPARE_OP               ==
          576_578  POP_JUMP_IF_FALSE   644  'to 644'

 L. 507       580  LOAD_STR                 'target_track'
              582  STORE_GLOBAL             g_mode

 L. 508       584  LOAD_STR                 'color_track'
              586  STORE_GLOBAL             g_target_mode

 L. 509       588  LOAD_GLOBAL              np
              590  LOAD_METHOD              array
              592  LOAD_CONST               0
              594  LOAD_CONST               43
              596  LOAD_CONST               46
              598  BUILD_LIST_3          3 
              600  CALL_METHOD_1         1  '1 positional argument'
              602  STORE_GLOBAL             color_lower

 L. 510       604  LOAD_GLOBAL              np
              606  LOAD_METHOD              array
              608  LOAD_CONST               10
              610  LOAD_CONST               255
              612  LOAD_CONST               255
              614  BUILD_LIST_3          3 
              616  CALL_METHOD_1         1  '1 positional argument'
              618  STORE_GLOBAL             color_upper

 L. 511       620  LOAD_CONST               1500
              622  DUP_TOP          
              624  STORE_FAST               'target_valuex'
              626  STORE_FAST               'target_valuey'

 L. 512       628  LOAD_GLOBAL              robot
              630  LOAD_METHOD              Servo_control
              632  LOAD_CONST               1500
              634  LOAD_CONST               1500
              636  CALL_METHOD_2         2  '2 positional arguments'
              638  POP_TOP          
          640_642  JUMP_ABSOLUTE      1034  'to 1034'
            644_0  COME_FROM           576  '576'

 L. 513       644  LOAD_FAST                'target_select'
              646  LOAD_STR                 '2'
              648  COMPARE_OP               ==
          650_652  POP_JUMP_IF_FALSE   718  'to 718'

 L. 514       654  LOAD_STR                 'target_track'
              656  STORE_GLOBAL             g_mode

 L. 515       658  LOAD_STR                 'color_track'
              660  STORE_GLOBAL             g_target_mode

 L. 516       662  LOAD_GLOBAL              np
              664  LOAD_METHOD              array
              666  LOAD_CONST               35
              668  LOAD_CONST               43
              670  LOAD_CONST               46
              672  BUILD_LIST_3          3 
              674  CALL_METHOD_1         1  '1 positional argument'
              676  STORE_GLOBAL             color_lower

 L. 517       678  LOAD_GLOBAL              np
              680  LOAD_METHOD              array
              682  LOAD_CONST               77
              684  LOAD_CONST               255
              686  LOAD_CONST               255
              688  BUILD_LIST_3          3 
              690  CALL_METHOD_1         1  '1 positional argument'
              692  STORE_GLOBAL             color_upper

 L. 518       694  LOAD_CONST               1500
              696  DUP_TOP          
              698  STORE_FAST               'target_valuex'
              700  STORE_FAST               'target_valuey'

 L. 519       702  LOAD_GLOBAL              robot
              704  LOAD_METHOD              Servo_control
              706  LOAD_CONST               1500
              708  LOAD_CONST               1500
              710  CALL_METHOD_2         2  '2 positional arguments'
              712  POP_TOP          
          714_716  JUMP_ABSOLUTE      1034  'to 1034'
            718_0  COME_FROM           650  '650'

 L. 520       718  LOAD_FAST                'target_select'
              720  LOAD_STR                 '3'
              722  COMPARE_OP               ==
          724_726  POP_JUMP_IF_FALSE   790  'to 790'

 L. 521       728  LOAD_STR                 'target_track'
              730  STORE_GLOBAL             g_mode

 L. 522       732  LOAD_STR                 'color_track'
              734  STORE_GLOBAL             g_target_mode

 L. 523       736  LOAD_GLOBAL              np
              738  LOAD_METHOD              array
              740  LOAD_CONST               100
              742  LOAD_CONST               43
              744  LOAD_CONST               46
              746  BUILD_LIST_3          3 
              748  CALL_METHOD_1         1  '1 positional argument'
              750  STORE_GLOBAL             color_lower

 L. 524       752  LOAD_GLOBAL              np
              754  LOAD_METHOD              array
              756  LOAD_CONST               124
              758  LOAD_CONST               255
              760  LOAD_CONST               255
              762  BUILD_LIST_3          3 
              764  CALL_METHOD_1         1  '1 positional argument'
              766  STORE_GLOBAL             color_upper

 L. 525       768  LOAD_CONST               1500
              770  DUP_TOP          
              772  STORE_FAST               'target_valuex'
              774  STORE_FAST               'target_valuey'

 L. 526       776  LOAD_GLOBAL              robot
              778  LOAD_METHOD              Servo_control
              780  LOAD_CONST               1500
              782  LOAD_CONST               1500
              784  CALL_METHOD_2         2  '2 positional arguments'
              786  POP_TOP          
              788  JUMP_FORWARD       1024  'to 1024'
            790_0  COME_FROM           724  '724'

 L. 527       790  LOAD_FAST                'target_select'
              792  LOAD_STR                 '4'
              794  COMPARE_OP               ==
          796_798  POP_JUMP_IF_FALSE   862  'to 862'

 L. 528       800  LOAD_STR                 'target_track'
              802  STORE_GLOBAL             g_mode

 L. 529       804  LOAD_STR                 'color_track'
              806  STORE_GLOBAL             g_target_mode

 L. 530       808  LOAD_GLOBAL              np
              810  LOAD_METHOD              array
              812  LOAD_CONST               26
              814  LOAD_CONST               43
              816  LOAD_CONST               46
              818  BUILD_LIST_3          3 
              820  CALL_METHOD_1         1  '1 positional argument'
              822  STORE_GLOBAL             color_lower

 L. 531       824  LOAD_GLOBAL              np
              826  LOAD_METHOD              array
              828  LOAD_CONST               34
              830  LOAD_CONST               255
              832  LOAD_CONST               255
              834  BUILD_LIST_3          3 
              836  CALL_METHOD_1         1  '1 positional argument'
              838  STORE_GLOBAL             color_upper

 L. 532       840  LOAD_CONST               1500
              842  DUP_TOP          
              844  STORE_FAST               'target_valuex'
              846  STORE_FAST               'target_valuey'

 L. 533       848  LOAD_GLOBAL              robot
              850  LOAD_METHOD              Servo_control
              852  LOAD_CONST               1500
              854  LOAD_CONST               1500
              856  CALL_METHOD_2         2  '2 positional arguments'
              858  POP_TOP          
              860  JUMP_FORWARD       1024  'to 1024'
            862_0  COME_FROM           796  '796'

 L. 534       862  LOAD_FAST                'target_select'
              864  LOAD_STR                 '5'
              866  COMPARE_OP               ==
          868_870  POP_JUMP_IF_FALSE   934  'to 934'

 L. 535       872  LOAD_STR                 'target_track'
              874  STORE_GLOBAL             g_mode

 L. 536       876  LOAD_STR                 'color_track'
              878  STORE_GLOBAL             g_target_mode

 L. 537       880  LOAD_GLOBAL              np
              882  LOAD_METHOD              array
              884  LOAD_CONST               11
              886  LOAD_CONST               43
              888  LOAD_CONST               46
              890  BUILD_LIST_3          3 
              892  CALL_METHOD_1         1  '1 positional argument'
              894  STORE_GLOBAL             color_lower

 L. 538       896  LOAD_GLOBAL              np
              898  LOAD_METHOD              array
              900  LOAD_CONST               25
              902  LOAD_CONST               255
              904  LOAD_CONST               255
              906  BUILD_LIST_3          3 
              908  CALL_METHOD_1         1  '1 positional argument'
              910  STORE_GLOBAL             color_upper

 L. 539       912  LOAD_CONST               1500
              914  DUP_TOP          
              916  STORE_FAST               'target_valuex'
              918  STORE_FAST               'target_valuey'

 L. 540       920  LOAD_GLOBAL              robot
              922  LOAD_METHOD              Servo_control
              924  LOAD_CONST               1500
              926  LOAD_CONST               1500
              928  CALL_METHOD_2         2  '2 positional arguments'
              930  POP_TOP          
              932  JUMP_FORWARD       1024  'to 1024'
            934_0  COME_FROM           868  '868'

 L. 541       934  LOAD_FAST                'target_select'
              936  LOAD_STR                 '6'
              938  COMPARE_OP               ==
          940_942  POP_JUMP_IF_FALSE  1006  'to 1006'

 L. 542       944  LOAD_STR                 '0'
              946  STORE_GLOBAL             g_target_mode

 L. 543       948  LOAD_STR                 '0'
              950  STORE_GLOBAL             g_mode

 L. 544       952  LOAD_GLOBAL              np
              954  LOAD_METHOD              array
              956  LOAD_CONST               156
              958  LOAD_CONST               43
              960  LOAD_CONST               46
              962  BUILD_LIST_3          3 
              964  CALL_METHOD_1         1  '1 positional argument'
              966  STORE_GLOBAL             color_lower

 L. 545       968  LOAD_GLOBAL              np
              970  LOAD_METHOD              array
              972  LOAD_CONST               180
              974  LOAD_CONST               255
              976  LOAD_CONST               255
              978  BUILD_LIST_3          3 
              980  CALL_METHOD_1         1  '1 positional argument'
              982  STORE_GLOBAL             color_upper

 L. 546       984  LOAD_CONST               1500
              986  DUP_TOP          
              988  STORE_FAST               'target_valuex'
              990  STORE_FAST               'target_valuey'

 L. 547       992  LOAD_GLOBAL              robot
              994  LOAD_METHOD              Servo_control
              996  LOAD_CONST               1500
              998  LOAD_CONST               1500
             1000  CALL_METHOD_2         2  '2 positional arguments'
             1002  POP_TOP          
             1004  JUMP_FORWARD       1024  'to 1024'
           1006_0  COME_FROM           940  '940'

 L. 548      1006  LOAD_FAST                'target_select'
             1008  LOAD_STR                 '7'
             1010  COMPARE_OP               ==
         1012_1014  POP_JUMP_IF_FALSE  1034  'to 1034'

 L. 549      1016  LOAD_STR                 'target_track'
             1018  STORE_GLOBAL             g_mode

 L. 550      1020  LOAD_STR                 'face_track'
             1022  STORE_GLOBAL             g_target_mode
           1024_0  COME_FROM          1004  '1004'
           1024_1  COME_FROM           932  '932'
           1024_2  COME_FROM           860  '860'
           1024_3  COME_FROM           788  '788'
             1024  JUMP_FORWARD       1034  'to 1034'
           1026_0  COME_FROM           516  '516'

 L. 552      1026  LOAD_GLOBAL              print
             1028  LOAD_STR                 'cmd-04 expression parse failure!'
             1030  CALL_FUNCTION_1       1  '1 positional argument'
             1032  POP_TOP          
           1034_0  COME_FROM          1024  '1024'
           1034_1  COME_FROM          1012  '1012'
             1034  POP_BLOCK        
             1036  JUMP_FORWARD       3526  'to 3526'
           1038_0  COME_FROM_EXCEPT    506  '506'

 L. 553      1038  POP_TOP          
             1040  POP_TOP          
             1042  POP_TOP          

 L. 554      1044  LOAD_GLOBAL              print
             1046  LOAD_STR                 'cmd-04 parse failure!'
             1048  CALL_FUNCTION_1       1  '1 positional argument'
             1050  POP_TOP          

 L. 555      1052  POP_EXCEPT       
             1054  JUMP_FORWARD       3526  'to 3526'
             1056  END_FINALLY      
         1058_1060  JUMP_FORWARD       3526  'to 3526'
           1062_0  COME_FROM           482  '482'

 L. 557      1062  LOAD_FAST                'cmd_function'
             1064  LOAD_STR                 '05'
             1066  COMPARE_OP               ==
         1068_1070  POP_JUMP_IF_FALSE  1264  'to 1264'

 L. 558      1072  LOAD_FAST                'cmd'
             1074  LOAD_CONST               -1
             1076  BINARY_SUBSCR    
             1078  LOAD_STR                 '#'
             1080  COMPARE_OP               ==
         1082_1084  POP_JUMP_IF_FALSE  1252  'to 1252'
             1086  LOAD_FAST                'cmd'
             1088  LOAD_CONST               0
             1090  LOAD_CONST               4
             1092  BUILD_SLICE_2         2 
             1094  BINARY_SUBSCR    
             1096  LOAD_STR                 '$05,'
             1098  COMPARE_OP               ==
         1100_1102  POP_JUMP_IF_FALSE  1252  'to 1252'

 L. 559      1104  LOAD_FAST                'cmd'
             1106  LOAD_CONST               4
             1108  LOAD_CONST               -1
             1110  BUILD_SLICE_2         2 
             1112  BINARY_SUBSCR    
             1114  STORE_FAST               'Voice_text'

 L. 560      1116  LOAD_FAST                'Voice_text'
             1118  LOAD_STR                 ''
             1120  COMPARE_OP               !=
         1122_1124  POP_JUMP_IF_FALSE  1260  'to 1260'

 L. 561      1126  LOAD_GLOBAL              print
             1128  LOAD_STR                 'Voice_txt: %s'
             1130  LOAD_FAST                'Voice_text'
             1132  BINARY_MODULO    
             1134  CALL_FUNCTION_1       1  '1 positional argument'
             1136  POP_TOP          

 L. 562      1138  LOAD_GLOBAL              client
             1140  LOAD_ATTR                synthesis
             1142  LOAD_FAST                'Voice_text'

 L. 563      1144  LOAD_CONST               2
             1146  LOAD_CONST               15
             1148  LOAD_CONST               2
             1150  LOAD_CONST               ('spd', 'vol', 'per')
             1152  BUILD_CONST_KEY_MAP_3     3 
             1154  LOAD_CONST               ('text', 'options')
             1156  CALL_FUNCTION_KW_2     2  '2 total positional and keyword args'
             1158  STORE_FAST               'result'

 L. 565      1160  LOAD_GLOBAL              isinstance
             1162  LOAD_FAST                'result'
             1164  LOAD_GLOBAL              dict
             1166  CALL_FUNCTION_2       2  '2 positional arguments'
         1168_1170  POP_JUMP_IF_TRUE   1242  'to 1242'

 L. 566      1172  LOAD_GLOBAL              open
             1174  LOAD_STR                 '/home/pi/yahboom-raspblock/audio.mp3'
             1176  LOAD_STR                 'wb'
             1178  CALL_FUNCTION_2       2  '2 positional arguments'
             1180  SETUP_WITH         1234  'to 1234'
             1182  STORE_FAST               'f'

 L. 567      1184  LOAD_FAST                'f'
             1186  LOAD_METHOD              write
             1188  LOAD_FAST                'result'
             1190  CALL_METHOD_1         1  '1 positional argument'
             1192  POP_TOP          

 L. 569      1194  LOAD_GLOBAL              pygame
             1196  LOAD_ATTR                mixer
             1198  LOAD_METHOD              init
             1200  CALL_METHOD_0         0  '0 positional arguments'
             1202  POP_TOP          

 L. 570      1204  LOAD_GLOBAL              pygame
             1206  LOAD_ATTR                mixer
             1208  LOAD_ATTR                music
             1210  LOAD_METHOD              load
             1212  LOAD_STR                 '/home/pi/yahboom-raspblock/audio.mp3'
             1214  CALL_METHOD_1         1  '1 positional argument'
             1216  POP_TOP          

 L. 571      1218  LOAD_GLOBAL              pygame
             1220  LOAD_ATTR                mixer
             1222  LOAD_ATTR                music
             1224  LOAD_METHOD              play
             1226  CALL_METHOD_0         0  '0 positional arguments'
             1228  POP_TOP          
             1230  POP_BLOCK        
             1232  LOAD_CONST               None
           1234_0  COME_FROM_WITH     1180  '1180'
             1234  WITH_CLEANUP_START
             1236  WITH_CLEANUP_FINISH
             1238  END_FINALLY      
             1240  JUMP_FORWARD       1250  'to 1250'
           1242_0  COME_FROM          1168  '1168'

 L. 573      1242  LOAD_GLOBAL              print
             1244  LOAD_FAST                'result'
             1246  CALL_FUNCTION_1       1  '1 positional argument'
             1248  POP_TOP          
           1250_0  COME_FROM          1240  '1240'
             1250  JUMP_FORWARD       3526  'to 3526'
           1252_0  COME_FROM          1100  '1100'
           1252_1  COME_FROM          1082  '1082'

 L. 575      1252  LOAD_GLOBAL              print
             1254  LOAD_STR                 'cmd-05 expression parse failure!'
             1256  CALL_FUNCTION_1       1  '1 positional argument'
             1258  POP_TOP          
           1260_0  COME_FROM          1122  '1122'
         1260_1262  JUMP_FORWARD       3526  'to 3526'
           1264_0  COME_FROM          1068  '1068'

 L. 577      1264  LOAD_FAST                'cmd_function'
             1266  LOAD_STR                 '06'
             1268  COMPARE_OP               ==
         1270_1272  POP_JUMP_IF_FALSE  1502  'to 1502'

 L. 578      1274  LOAD_GLOBAL              re
             1276  LOAD_METHOD              compile
             1278  LOAD_STR                 '^\\$06,(?P<Recognize_option>[^ ]*)#'
             1280  CALL_METHOD_1         1  '1 positional argument'
             1282  STORE_FAST               'reg'

 L. 579      1284  LOAD_FAST                'reg'
             1286  LOAD_METHOD              match
             1288  LOAD_FAST                'cmd'
             1290  CALL_METHOD_1         1  '1 positional argument'
             1292  STORE_FAST               'regMatch'

 L. 580      1294  SETUP_EXCEPT       1478  'to 1478'

 L. 581      1296  LOAD_FAST                'regMatch'
             1298  LOAD_CONST               None
             1300  COMPARE_OP               !=
         1302_1304  POP_JUMP_IF_FALSE  1466  'to 1466'

 L. 582      1306  LOAD_FAST                'regMatch'
             1308  LOAD_METHOD              groupdict
             1310  CALL_METHOD_0         0  '0 positional arguments'
             1312  STORE_FAST               'linebits'

 L. 583      1314  LOAD_FAST                'linebits'
             1316  LOAD_STR                 'Recognize_option'
             1318  BINARY_SUBSCR    
             1320  STORE_FAST               'Recognize_option'

 L. 584      1322  LOAD_FAST                'Recognize_option'
             1324  LOAD_CONST               0
             1326  BINARY_SUBSCR    
             1328  LOAD_STR                 '0'
             1330  COMPARE_OP               ==
         1332_1334  POP_JUMP_IF_FALSE  1342  'to 1342'

 L. 585      1336  LOAD_STR                 'close'
             1338  STORE_GLOBAL             g_tag_identify_switch
             1340  JUMP_FORWARD       1360  'to 1360'
           1342_0  COME_FROM          1332  '1332'

 L. 586      1342  LOAD_FAST                'Recognize_option'
             1344  LOAD_CONST               0
             1346  BINARY_SUBSCR    
             1348  LOAD_STR                 '1'
             1350  COMPARE_OP               ==
         1352_1354  POP_JUMP_IF_FALSE  1360  'to 1360'

 L. 587      1356  LOAD_STR                 'open'
             1358  STORE_GLOBAL             g_tag_identify_switch
           1360_0  COME_FROM          1352  '1352'
           1360_1  COME_FROM          1340  '1340'

 L. 588      1360  LOAD_FAST                'Recognize_option'
             1362  LOAD_CONST               1
             1364  BINARY_SUBSCR    
             1366  LOAD_STR                 '1'
             1368  COMPARE_OP               ==
         1370_1372  POP_JUMP_IF_FALSE  1380  'to 1380'

 L. 589      1374  LOAD_STR                 'qrcode'
             1376  STORE_GLOBAL             g_tag_select
             1378  JUMP_FORWARD       1418  'to 1418'
           1380_0  COME_FROM          1370  '1370'

 L. 590      1380  LOAD_FAST                'Recognize_option'
             1382  LOAD_CONST               1
             1384  BINARY_SUBSCR    
             1386  LOAD_STR                 '2'
             1388  COMPARE_OP               ==
         1390_1392  POP_JUMP_IF_FALSE  1400  'to 1400'

 L. 591      1394  LOAD_STR                 'object'
             1396  STORE_GLOBAL             g_tag_select
             1398  JUMP_FORWARD       1418  'to 1418'
           1400_0  COME_FROM          1390  '1390'

 L. 592      1400  LOAD_FAST                'Recognize_option'
             1402  LOAD_CONST               1
             1404  BINARY_SUBSCR    
             1406  LOAD_STR                 '3'
             1408  COMPARE_OP               ==
         1410_1412  POP_JUMP_IF_FALSE  1418  'to 1418'

 L. 593      1414  LOAD_STR                 'gesture'
             1416  STORE_GLOBAL             g_tag_select
           1418_0  COME_FROM          1410  '1410'
           1418_1  COME_FROM          1398  '1398'
           1418_2  COME_FROM          1378  '1378'

 L. 595      1418  LOAD_FAST                'Recognize_option'
             1420  LOAD_CONST               2
             1422  BINARY_SUBSCR    
             1424  LOAD_STR                 '0'
             1426  COMPARE_OP               ==
         1428_1430  POP_JUMP_IF_FALSE  1446  'to 1446'

 L. 596      1432  LOAD_STR                 'close'
             1434  STORE_GLOBAL             g_tag_brodcast_switch

 L. 597      1436  LOAD_STR                 ''
             1438  STORE_FAST               'identify_tag'

 L. 598      1440  LOAD_STR                 ''
             1442  STORE_FAST               'last_identify_tag'
             1444  JUMP_FORWARD       1464  'to 1464'
           1446_0  COME_FROM          1428  '1428'

 L. 599      1446  LOAD_FAST                'Recognize_option'
             1448  LOAD_CONST               2
             1450  BINARY_SUBSCR    
             1452  LOAD_STR                 '1'
             1454  COMPARE_OP               ==
         1456_1458  POP_JUMP_IF_FALSE  1474  'to 1474'

 L. 600      1460  LOAD_STR                 'open'
             1462  STORE_GLOBAL             g_tag_brodcast_switch
           1464_0  COME_FROM          1444  '1444'
             1464  JUMP_FORWARD       1474  'to 1474'
           1466_0  COME_FROM          1302  '1302'

 L. 602      1466  LOAD_GLOBAL              print
             1468  LOAD_STR                 'cmd-06 expression parse failure!'
             1470  CALL_FUNCTION_1       1  '1 positional argument'
             1472  POP_TOP          
           1474_0  COME_FROM          1464  '1464'
           1474_1  COME_FROM          1456  '1456'
             1474  POP_BLOCK        
             1476  JUMP_FORWARD       3526  'to 3526'
           1478_0  COME_FROM_EXCEPT   1294  '1294'

 L. 603      1478  POP_TOP          
             1480  POP_TOP          
             1482  POP_TOP          

 L. 604      1484  LOAD_GLOBAL              print
             1486  LOAD_STR                 'cmd-06 parse failure!'
             1488  CALL_FUNCTION_1       1  '1 positional argument'
             1490  POP_TOP          

 L. 605      1492  POP_EXCEPT       
             1494  JUMP_FORWARD       3526  'to 3526'
             1496  END_FINALLY      
         1498_1500  JUMP_FORWARD       3526  'to 3526'
           1502_0  COME_FROM          1270  '1270'

 L. 607      1502  LOAD_FAST                'cmd_function'
             1504  LOAD_STR                 '07'
             1506  COMPARE_OP               ==
         1508_1510  POP_JUMP_IF_FALSE  1804  'to 1804'

 L. 608      1512  LOAD_GLOBAL              re
             1514  LOAD_METHOD              compile
             1516  LOAD_STR                 '^\\$07,(?P<Presentation_Mode>[^ ]*)#'
             1518  CALL_METHOD_1         1  '1 positional argument'
             1520  STORE_FAST               'reg'

 L. 609      1522  LOAD_FAST                'reg'
             1524  LOAD_METHOD              match
             1526  LOAD_FAST                'cmd'
             1528  CALL_METHOD_1         1  '1 positional argument'
             1530  STORE_FAST               'regMatch'

 L. 610      1532  SETUP_EXCEPT       1780  'to 1780'

 L. 611      1534  LOAD_FAST                'regMatch'
             1536  LOAD_CONST               None
             1538  COMPARE_OP               !=
         1540_1542  POP_JUMP_IF_FALSE  1768  'to 1768'

 L. 612      1544  LOAD_FAST                'regMatch'
             1546  LOAD_METHOD              groupdict
             1548  CALL_METHOD_0         0  '0 positional arguments'
             1550  STORE_FAST               'linebits'

 L. 613      1552  LOAD_FAST                'linebits'
             1554  LOAD_STR                 'Presentation_Mode'
             1556  BINARY_SUBSCR    
             1558  STORE_FAST               'Presentation_Mode'

 L. 614      1560  LOAD_FAST                'Presentation_Mode'
             1562  LOAD_STR                 '0'
             1564  COMPARE_OP               ==
         1566_1568  POP_JUMP_IF_FALSE  1612  'to 1612'

 L. 615      1570  LOAD_STR                 '0'
             1572  STORE_GLOBAL             g_presentation_mode

 L. 616      1574  LOAD_GLOBAL              pygame
             1576  LOAD_ATTR                mixer
             1578  LOAD_METHOD              init
             1580  CALL_METHOD_0         0  '0 positional arguments'
             1582  POP_TOP          

 L. 617      1584  LOAD_GLOBAL              pygame
             1586  LOAD_ATTR                mixer
             1588  LOAD_ATTR                music
             1590  LOAD_METHOD              load
             1592  LOAD_STR                 '/home/pi/yahboom-raspblock/ModeClose.mp3'
             1594  CALL_METHOD_1         1  '1 positional argument'
             1596  POP_TOP          

 L. 618      1598  LOAD_GLOBAL              pygame
             1600  LOAD_ATTR                mixer
             1602  LOAD_ATTR                music
             1604  LOAD_METHOD              play
             1606  CALL_METHOD_0         0  '0 positional arguments'
             1608  POP_TOP          
             1610  JUMP_FORWARD       1766  'to 1766'
           1612_0  COME_FROM          1566  '1566'

 L. 619      1612  LOAD_FAST                'Presentation_Mode'
             1614  LOAD_STR                 '1'
             1616  COMPARE_OP               ==
         1618_1620  POP_JUMP_IF_FALSE  1664  'to 1664'

 L. 620      1622  LOAD_STR                 'around'
             1624  STORE_GLOBAL             g_presentation_mode

 L. 621      1626  LOAD_GLOBAL              pygame
             1628  LOAD_ATTR                mixer
             1630  LOAD_METHOD              init
             1632  CALL_METHOD_0         0  '0 positional arguments'
             1634  POP_TOP          

 L. 622      1636  LOAD_GLOBAL              pygame
             1638  LOAD_ATTR                mixer
             1640  LOAD_ATTR                music
             1642  LOAD_METHOD              load
             1644  LOAD_STR                 '/home/pi/yahboom-raspblock/surrondstart.mp3'
             1646  CALL_METHOD_1         1  '1 positional argument'
             1648  POP_TOP          

 L. 623      1650  LOAD_GLOBAL              pygame
             1652  LOAD_ATTR                mixer
             1654  LOAD_ATTR                music
             1656  LOAD_METHOD              play
             1658  CALL_METHOD_0         0  '0 positional arguments'
             1660  POP_TOP          
             1662  JUMP_FORWARD       1766  'to 1766'
           1664_0  COME_FROM          1618  '1618'

 L. 624      1664  LOAD_FAST                'Presentation_Mode'
             1666  LOAD_STR                 '2'
             1668  COMPARE_OP               ==
         1670_1672  POP_JUMP_IF_FALSE  1716  'to 1716'

 L. 625      1674  LOAD_STR                 'translation'
             1676  STORE_GLOBAL             g_presentation_mode

 L. 626      1678  LOAD_GLOBAL              pygame
             1680  LOAD_ATTR                mixer
             1682  LOAD_METHOD              init
             1684  CALL_METHOD_0         0  '0 positional arguments'
             1686  POP_TOP          

 L. 627      1688  LOAD_GLOBAL              pygame
             1690  LOAD_ATTR                mixer
             1692  LOAD_ATTR                music
             1694  LOAD_METHOD              load
             1696  LOAD_STR                 '/home/pi/yahboom-raspblock/TranslateStart.mp3'
             1698  CALL_METHOD_1         1  '1 positional argument'
             1700  POP_TOP          

 L. 628      1702  LOAD_GLOBAL              pygame
             1704  LOAD_ATTR                mixer
             1706  LOAD_ATTR                music
             1708  LOAD_METHOD              play
             1710  CALL_METHOD_0         0  '0 positional arguments'
             1712  POP_TOP          
             1714  JUMP_FORWARD       1766  'to 1766'
           1716_0  COME_FROM          1670  '1670'

 L. 629      1716  LOAD_FAST                'Presentation_Mode'
             1718  LOAD_STR                 '3'
             1720  COMPARE_OP               ==
         1722_1724  POP_JUMP_IF_FALSE  1776  'to 1776'

 L. 630      1726  LOAD_STR                 'stabilize'
             1728  STORE_GLOBAL             g_presentation_mode

 L. 631      1730  LOAD_GLOBAL              pygame
             1732  LOAD_ATTR                mixer
             1734  LOAD_METHOD              init
             1736  CALL_METHOD_0         0  '0 positional arguments'
             1738  POP_TOP          

 L. 632      1740  LOAD_GLOBAL              pygame
             1742  LOAD_ATTR                mixer
             1744  LOAD_ATTR                music
             1746  LOAD_METHOD              load
             1748  LOAD_STR                 '/home/pi/yahboom-raspblock/StandardStart.mp3'
             1750  CALL_METHOD_1         1  '1 positional argument'
             1752  POP_TOP          

 L. 633      1754  LOAD_GLOBAL              pygame
             1756  LOAD_ATTR                mixer
             1758  LOAD_ATTR                music
             1760  LOAD_METHOD              play
             1762  CALL_METHOD_0         0  '0 positional arguments'
             1764  POP_TOP          
           1766_0  COME_FROM          1714  '1714'
           1766_1  COME_FROM          1662  '1662'
           1766_2  COME_FROM          1610  '1610'
             1766  JUMP_FORWARD       1776  'to 1776'
           1768_0  COME_FROM          1540  '1540'

 L. 635      1768  LOAD_GLOBAL              print
             1770  LOAD_STR                 'cmd-07 expression parse failure!'
             1772  CALL_FUNCTION_1       1  '1 positional argument'
             1774  POP_TOP          
           1776_0  COME_FROM          1766  '1766'
           1776_1  COME_FROM          1722  '1722'
             1776  POP_BLOCK        
             1778  JUMP_FORWARD       3526  'to 3526'
           1780_0  COME_FROM_EXCEPT   1532  '1532'

 L. 636      1780  POP_TOP          
             1782  POP_TOP          
             1784  POP_TOP          

 L. 637      1786  LOAD_GLOBAL              print
             1788  LOAD_STR                 'cmd-07 parse failure!'
             1790  CALL_FUNCTION_1       1  '1 positional argument'
             1792  POP_TOP          

 L. 638      1794  POP_EXCEPT       
             1796  JUMP_FORWARD       3526  'to 3526'
             1798  END_FINALLY      
         1800_1802  JUMP_FORWARD       3526  'to 3526'
           1804_0  COME_FROM          1508  '1508'

 L. 640      1804  LOAD_FAST                'cmd_function'
             1806  LOAD_STR                 '08'
             1808  COMPARE_OP               ==
         1810_1812  POP_JUMP_IF_FALSE  1982  'to 1982'

 L. 641      1814  LOAD_GLOBAL              re
             1816  LOAD_METHOD              compile
             1818  LOAD_STR                 '^\\$08,(?P<Wheel>[^ ]*),(?P<Wheel_speed>[^ ]*)#'
             1820  CALL_METHOD_1         1  '1 positional argument'
             1822  STORE_FAST               'reg'

 L. 642      1824  LOAD_FAST                'reg'
             1826  LOAD_METHOD              match
             1828  LOAD_FAST                'cmd'
             1830  CALL_METHOD_1         1  '1 positional argument'
             1832  STORE_FAST               'regMatch'

 L. 643      1834  SETUP_EXCEPT       1958  'to 1958'

 L. 644      1836  LOAD_FAST                'regMatch'
             1838  LOAD_CONST               None
             1840  COMPARE_OP               !=
         1842_1844  POP_JUMP_IF_FALSE  1946  'to 1946'

 L. 645      1846  LOAD_FAST                'regMatch'
             1848  LOAD_METHOD              groupdict
             1850  CALL_METHOD_0         0  '0 positional arguments'
             1852  STORE_FAST               'linebits'

 L. 646      1854  LOAD_FAST                'linebits'
             1856  LOAD_STR                 'Wheel'
             1858  BINARY_SUBSCR    
             1860  STORE_FAST               'Wheel'

 L. 647      1862  LOAD_GLOBAL              int
             1864  LOAD_FAST                'linebits'
             1866  LOAD_STR                 'Wheel_speed'
             1868  BINARY_SUBSCR    
             1870  CALL_FUNCTION_1       1  '1 positional argument'
             1872  STORE_FAST               'Wheel_speed'

 L. 648      1874  LOAD_GLOBAL              print
             1876  LOAD_FAST                'Wheel_speed'
             1878  CALL_FUNCTION_1       1  '1 positional argument'
             1880  POP_TOP          

 L. 649      1882  LOAD_FAST                'Wheel'
             1884  LOAD_STR                 '1'
             1886  COMPARE_OP               ==
         1888_1890  POP_JUMP_IF_FALSE  1898  'to 1898'

 L. 650      1892  LOAD_FAST                'Wheel_speed'
             1894  STORE_GLOBAL             Speed_WheelD
             1896  JUMP_FORWARD       1944  'to 1944'
           1898_0  COME_FROM          1888  '1888'

 L. 651      1898  LOAD_FAST                'Wheel'
             1900  LOAD_STR                 '2'
             1902  COMPARE_OP               ==
         1904_1906  POP_JUMP_IF_FALSE  1914  'to 1914'

 L. 652      1908  LOAD_FAST                'Wheel_speed'
             1910  STORE_GLOBAL             Speed_WheelC
             1912  JUMP_FORWARD       1944  'to 1944'
           1914_0  COME_FROM          1904  '1904'

 L. 653      1914  LOAD_FAST                'Wheel'
             1916  LOAD_STR                 '3'
             1918  COMPARE_OP               ==
         1920_1922  POP_JUMP_IF_FALSE  1930  'to 1930'

 L. 654      1924  LOAD_FAST                'Wheel_speed'
             1926  STORE_GLOBAL             Speed_WheelA
             1928  JUMP_FORWARD       1944  'to 1944'
           1930_0  COME_FROM          1920  '1920'

 L. 655      1930  LOAD_FAST                'Wheel'
             1932  LOAD_STR                 '4'
             1934  COMPARE_OP               ==
         1936_1938  POP_JUMP_IF_FALSE  1954  'to 1954'

 L. 656      1940  LOAD_FAST                'Wheel_speed'
             1942  STORE_GLOBAL             Speed_WheelB
           1944_0  COME_FROM          1928  '1928'
           1944_1  COME_FROM          1912  '1912'
           1944_2  COME_FROM          1896  '1896'
             1944  JUMP_FORWARD       1954  'to 1954'
           1946_0  COME_FROM          1842  '1842'

 L. 658      1946  LOAD_GLOBAL              print
             1948  LOAD_STR                 'cmd-08 expression parse failure!'
             1950  CALL_FUNCTION_1       1  '1 positional argument'
             1952  POP_TOP          
           1954_0  COME_FROM          1944  '1944'
           1954_1  COME_FROM          1936  '1936'
             1954  POP_BLOCK        
             1956  JUMP_FORWARD       3526  'to 3526'
           1958_0  COME_FROM_EXCEPT   1834  '1834'

 L. 659      1958  POP_TOP          
             1960  POP_TOP          
             1962  POP_TOP          

 L. 660      1964  LOAD_GLOBAL              print
             1966  LOAD_STR                 'cmd-08 parse failure!'
             1968  CALL_FUNCTION_1       1  '1 positional argument'
             1970  POP_TOP          

 L. 661      1972  POP_EXCEPT       
             1974  JUMP_FORWARD       3526  'to 3526'
             1976  END_FINALLY      
         1978_1980  JUMP_FORWARD       3526  'to 3526'
           1982_0  COME_FROM          1810  '1810'

 L. 663      1982  LOAD_FAST                'cmd_function'
             1984  LOAD_STR                 '09'
             1986  COMPARE_OP               ==
         1988_1990  POP_JUMP_IF_FALSE  2118  'to 2118'

 L. 664      1992  LOAD_GLOBAL              re
             1994  LOAD_METHOD              compile
             1996  LOAD_STR                 '^\\$09,(?P<WheelA_speed>[^ ]*),(?P<WheelB_speed>[^ ]*),(?P<WheelC_speed>[^ ]*),(?P<WheelD_speed>[^ ]*)#'
             1998  CALL_METHOD_1         1  '1 positional argument'
             2000  STORE_FAST               'reg'

 L. 665      2002  LOAD_FAST                'reg'
             2004  LOAD_METHOD              match
             2006  LOAD_FAST                'cmd'
             2008  CALL_METHOD_1         1  '1 positional argument'
             2010  STORE_FAST               'regMatch'

 L. 666      2012  SETUP_EXCEPT       2094  'to 2094'

 L. 667      2014  LOAD_FAST                'regMatch'
             2016  LOAD_CONST               None
             2018  COMPARE_OP               !=
         2020_2022  POP_JUMP_IF_FALSE  2082  'to 2082'

 L. 668      2024  LOAD_FAST                'regMatch'
             2026  LOAD_METHOD              groupdict
             2028  CALL_METHOD_0         0  '0 positional arguments'
             2030  STORE_FAST               'linebits'

 L. 669      2032  LOAD_GLOBAL              int
             2034  LOAD_FAST                'linebits'
             2036  LOAD_STR                 'WheelA_speed'
             2038  BINARY_SUBSCR    
             2040  CALL_FUNCTION_1       1  '1 positional argument'
             2042  STORE_GLOBAL             Speed_WheelD

 L. 670      2044  LOAD_GLOBAL              int
             2046  LOAD_FAST                'linebits'
             2048  LOAD_STR                 'WheelB_speed'
             2050  BINARY_SUBSCR    
             2052  CALL_FUNCTION_1       1  '1 positional argument'
             2054  STORE_GLOBAL             Speed_WheelC

 L. 671      2056  LOAD_GLOBAL              int
             2058  LOAD_FAST                'linebits'
             2060  LOAD_STR                 'WheelC_speed'
             2062  BINARY_SUBSCR    
             2064  CALL_FUNCTION_1       1  '1 positional argument'
             2066  STORE_GLOBAL             Speed_WheelA

 L. 672      2068  LOAD_GLOBAL              int
             2070  LOAD_FAST                'linebits'
             2072  LOAD_STR                 'WheelD_speed'
             2074  BINARY_SUBSCR    
             2076  CALL_FUNCTION_1       1  '1 positional argument'
             2078  STORE_GLOBAL             Speed_WheelB
             2080  JUMP_FORWARD       2090  'to 2090'
           2082_0  COME_FROM          2020  '2020'

 L. 675      2082  LOAD_GLOBAL              print
             2084  LOAD_STR                 'cmd-09 expression parse failure!'
             2086  CALL_FUNCTION_1       1  '1 positional argument'
             2088  POP_TOP          
           2090_0  COME_FROM          2080  '2080'
             2090  POP_BLOCK        
             2092  JUMP_FORWARD       3526  'to 3526'
           2094_0  COME_FROM_EXCEPT   2012  '2012'

 L. 676      2094  POP_TOP          
             2096  POP_TOP          
             2098  POP_TOP          

 L. 677      2100  LOAD_GLOBAL              print
             2102  LOAD_STR                 'cmd-09 parse failure!'
             2104  CALL_FUNCTION_1       1  '1 positional argument'
             2106  POP_TOP          

 L. 678      2108  POP_EXCEPT       
             2110  JUMP_FORWARD       3526  'to 3526'
             2112  END_FINALLY      
         2114_2116  JUMP_FORWARD       3526  'to 3526'
           2118_0  COME_FROM          1988  '1988'

 L. 680      2118  LOAD_FAST                'cmd_function'
             2120  LOAD_STR                 '10'
             2122  COMPARE_OP               ==
         2124_2126  POP_JUMP_IF_FALSE  2256  'to 2256'

 L. 681      2128  LOAD_GLOBAL              re
             2130  LOAD_METHOD              compile
             2132  LOAD_STR                 '^\\$10,(?P<Buzzer_state>[^ ]*)#'
             2134  CALL_METHOD_1         1  '1 positional argument'
             2136  STORE_FAST               'reg'

 L. 682      2138  LOAD_FAST                'reg'
             2140  LOAD_METHOD              match
             2142  LOAD_FAST                'cmd'
             2144  CALL_METHOD_1         1  '1 positional argument'
             2146  STORE_FAST               'regMatch'

 L. 683      2148  SETUP_EXCEPT       2232  'to 2232'

 L. 684      2150  LOAD_FAST                'regMatch'
             2152  LOAD_CONST               None
             2154  COMPARE_OP               !=
         2156_2158  POP_JUMP_IF_FALSE  2220  'to 2220'

 L. 685      2160  LOAD_FAST                'regMatch'
             2162  LOAD_METHOD              groupdict
             2164  CALL_METHOD_0         0  '0 positional arguments'
             2166  STORE_FAST               'linebits'

 L. 686      2168  LOAD_FAST                'linebits'
             2170  LOAD_STR                 'Buzzer_state'
             2172  BINARY_SUBSCR    
             2174  STORE_FAST               'Buzzer_state'

 L. 687      2176  LOAD_FAST                'Buzzer_state'
             2178  LOAD_STR                 '0'
             2180  COMPARE_OP               ==
         2182_2184  POP_JUMP_IF_FALSE  2198  'to 2198'

 L. 688      2186  LOAD_GLOBAL              robot
             2188  LOAD_METHOD              Buzzer_control
             2190  LOAD_CONST               0
             2192  CALL_METHOD_1         1  '1 positional argument'
             2194  POP_TOP          
             2196  JUMP_FORWARD       2218  'to 2218'
           2198_0  COME_FROM          2182  '2182'

 L. 689      2198  LOAD_FAST                'Buzzer_state'
             2200  LOAD_STR                 '1'
             2202  COMPARE_OP               ==
         2204_2206  POP_JUMP_IF_FALSE  2228  'to 2228'

 L. 690      2208  LOAD_GLOBAL              robot
             2210  LOAD_METHOD              Buzzer_control
             2212  LOAD_CONST               1
             2214  CALL_METHOD_1         1  '1 positional argument'
             2216  POP_TOP          
           2218_0  COME_FROM          2196  '2196'
             2218  JUMP_FORWARD       2228  'to 2228'
           2220_0  COME_FROM          2156  '2156'

 L. 692      2220  LOAD_GLOBAL              print
             2222  LOAD_STR                 'cmd-10 expression parse failure!'
             2224  CALL_FUNCTION_1       1  '1 positional argument'
             2226  POP_TOP          
           2228_0  COME_FROM          2218  '2218'
           2228_1  COME_FROM          2204  '2204'
             2228  POP_BLOCK        
             2230  JUMP_FORWARD       3526  'to 3526'
           2232_0  COME_FROM_EXCEPT   2148  '2148'

 L. 693      2232  POP_TOP          
             2234  POP_TOP          
             2236  POP_TOP          

 L. 694      2238  LOAD_GLOBAL              print
             2240  LOAD_STR                 'cmd-10 parse failure!'
             2242  CALL_FUNCTION_1       1  '1 positional argument'
             2244  POP_TOP          

 L. 695      2246  POP_EXCEPT       
             2248  JUMP_FORWARD       3526  'to 3526'
             2250  END_FINALLY      
         2252_2254  JUMP_FORWARD       3526  'to 3526'
           2256_0  COME_FROM          2124  '2124'

 L. 697      2256  LOAD_FAST                'cmd_function'
             2258  LOAD_STR                 '11'
             2260  COMPARE_OP               ==
         2262_2264  POP_JUMP_IF_FALSE  2446  'to 2446'

 L. 698      2266  LOAD_GLOBAL              re
             2268  LOAD_METHOD              compile
             2270  LOAD_STR                 '^\\$11,(?P<Auto_drive_state>[^ ]*)#'
             2272  CALL_METHOD_1         1  '1 positional argument'
             2274  STORE_FAST               'reg'

 L. 699      2276  LOAD_FAST                'reg'
             2278  LOAD_METHOD              match
             2280  LOAD_FAST                'cmd'
             2282  CALL_METHOD_1         1  '1 positional argument'
             2284  STORE_FAST               'regMatch'

 L. 700      2286  SETUP_EXCEPT       2422  'to 2422'

 L. 701      2288  LOAD_FAST                'regMatch'
             2290  LOAD_CONST               None
             2292  COMPARE_OP               !=
         2294_2296  POP_JUMP_IF_FALSE  2410  'to 2410'

 L. 702      2298  LOAD_FAST                'regMatch'
             2300  LOAD_METHOD              groupdict
             2302  CALL_METHOD_0         0  '0 positional arguments'
             2304  STORE_FAST               'linebits'

 L. 703      2306  LOAD_FAST                'linebits'
             2308  LOAD_STR                 'Auto_drive_state'
             2310  BINARY_SUBSCR    
             2312  STORE_FAST               'Auto_drive_state'

 L. 704      2314  LOAD_FAST                'Auto_drive_state'
             2316  LOAD_STR                 '0'
             2318  COMPARE_OP               ==
         2320_2322  POP_JUMP_IF_FALSE  2330  'to 2330'

 L. 705      2324  LOAD_STR                 'close'
             2326  STORE_GLOBAL             g_auto_drive_switch
             2328  JUMP_FORWARD       2408  'to 2408'
           2330_0  COME_FROM          2320  '2320'

 L. 709      2330  LOAD_FAST                'Auto_drive_state'
             2332  LOAD_STR                 '1'
             2334  COMPARE_OP               ==
         2336_2338  POP_JUMP_IF_FALSE  2418  'to 2418'

 L. 710      2340  LOAD_STR                 'open'
             2342  STORE_GLOBAL             g_auto_drive_switch

 L. 711      2344  LOAD_GLOBAL              updownpulse
             2346  LOAD_CONST               1500
             2348  COMPARE_OP               !=
         2350_2352  POP_JUMP_IF_FALSE  2364  'to 2364'

 L. 712      2354  LOAD_GLOBAL              leftrightpulse
             2356  STORE_FAST               'target_valuex'

 L. 713      2358  LOAD_GLOBAL              updownpulse
             2360  STORE_FAST               'target_valuey'
             2362  JUMP_FORWARD       2380  'to 2380'
           2364_0  COME_FROM          2350  '2350'

 L. 715      2364  LOAD_CONST               1550
             2366  STORE_FAST               'target_valuex'

 L. 716      2368  LOAD_CONST               2050
             2370  STORE_FAST               'target_valuey'

 L. 717      2372  LOAD_FAST                'target_valuex'
             2374  STORE_GLOBAL             leftrightpulse

 L. 718      2376  LOAD_FAST                'target_valuey'
             2378  STORE_GLOBAL             updownpulse
           2380_0  COME_FROM          2362  '2362'

 L. 719      2380  LOAD_GLOBAL              robot
             2382  LOAD_METHOD              Servo_control
             2384  LOAD_FAST                'target_valuex'
             2386  LOAD_FAST                'target_valuey'
             2388  CALL_METHOD_2         2  '2 positional arguments'
             2390  POP_TOP          

 L. 720      2392  LOAD_GLOBAL              print
             2394  LOAD_GLOBAL              leftrightpulse
             2396  CALL_FUNCTION_1       1  '1 positional argument'
             2398  POP_TOP          

 L. 721      2400  LOAD_GLOBAL              print
             2402  LOAD_GLOBAL              updownpulse
             2404  CALL_FUNCTION_1       1  '1 positional argument'
             2406  POP_TOP          
           2408_0  COME_FROM          2328  '2328'
             2408  JUMP_FORWARD       2418  'to 2418'
           2410_0  COME_FROM          2294  '2294'

 L. 723      2410  LOAD_GLOBAL              print
             2412  LOAD_STR                 'cmd-11 expression parse failure!'
             2414  CALL_FUNCTION_1       1  '1 positional argument'
             2416  POP_TOP          
           2418_0  COME_FROM          2408  '2408'
           2418_1  COME_FROM          2336  '2336'
             2418  POP_BLOCK        
             2420  JUMP_FORWARD       3526  'to 3526'
           2422_0  COME_FROM_EXCEPT   2286  '2286'

 L. 724      2422  POP_TOP          
             2424  POP_TOP          
             2426  POP_TOP          

 L. 725      2428  LOAD_GLOBAL              print
             2430  LOAD_STR                 'cmd-11 parse failure!'
             2432  CALL_FUNCTION_1       1  '1 positional argument'
             2434  POP_TOP          

 L. 726      2436  POP_EXCEPT       
             2438  JUMP_FORWARD       3526  'to 3526'
             2440  END_FINALLY      
         2442_2444  JUMP_FORWARD       3526  'to 3526'
           2446_0  COME_FROM          2262  '2262'

 L. 728      2446  LOAD_FAST                'cmd_function'
             2448  LOAD_STR                 '12'
             2450  COMPARE_OP               ==
         2452_2454  POP_JUMP_IF_FALSE  2584  'to 2584'

 L. 729      2456  LOAD_GLOBAL              re
             2458  LOAD_METHOD              compile
             2460  LOAD_STR                 '^\\$12,(?P<Speed_kind>[^ ]*),(?P<Max_speed>[^ ]*)#'
             2462  CALL_METHOD_1         1  '1 positional argument'
             2464  STORE_FAST               'reg'

 L. 730      2466  LOAD_FAST                'reg'
             2468  LOAD_METHOD              match
             2470  LOAD_FAST                'cmd'
             2472  CALL_METHOD_1         1  '1 positional argument'
             2474  STORE_FAST               'regMatch'

 L. 731      2476  SETUP_EXCEPT       2560  'to 2560'

 L. 732      2478  LOAD_FAST                'regMatch'
             2480  LOAD_CONST               None
             2482  COMPARE_OP               !=
         2484_2486  POP_JUMP_IF_FALSE  2548  'to 2548'

 L. 733      2488  LOAD_FAST                'regMatch'
             2490  LOAD_METHOD              groupdict
             2492  CALL_METHOD_0         0  '0 positional arguments'
             2494  STORE_FAST               'linebits'

 L. 734      2496  LOAD_FAST                'linebits'
             2498  LOAD_STR                 'Speed_kind'
             2500  BINARY_SUBSCR    
             2502  STORE_FAST               'Speed_kind'

 L. 735      2504  LOAD_GLOBAL              int
             2506  LOAD_FAST                'linebits'
             2508  LOAD_STR                 'Max_speed'
             2510  BINARY_SUBSCR    
             2512  CALL_FUNCTION_1       1  '1 positional argument'
             2514  STORE_FAST               'Max_speed'

 L. 736      2516  LOAD_FAST                'Speed_kind'
             2518  LOAD_STR                 '1'
             2520  COMPARE_OP               ==
         2522_2524  POP_JUMP_IF_FALSE  2532  'to 2532'

 L. 737      2526  LOAD_FAST                'Max_speed'
             2528  STORE_GLOBAL             Max_speed_XY
             2530  JUMP_FORWARD       2546  'to 2546'
           2532_0  COME_FROM          2522  '2522'

 L. 738      2532  LOAD_FAST                'Speed_kind'
             2534  LOAD_STR                 '2'
             2536  COMPARE_OP               ==
         2538_2540  POP_JUMP_IF_FALSE  2556  'to 2556'

 L. 739      2542  LOAD_FAST                'Max_speed'
             2544  STORE_GLOBAL             Max_speed_Z
           2546_0  COME_FROM          2530  '2530'
             2546  JUMP_FORWARD       2556  'to 2556'
           2548_0  COME_FROM          2484  '2484'

 L. 741      2548  LOAD_GLOBAL              print
             2550  LOAD_STR                 'cmd-12 expression parse failure!'
             2552  CALL_FUNCTION_1       1  '1 positional argument'
             2554  POP_TOP          
           2556_0  COME_FROM          2546  '2546'
           2556_1  COME_FROM          2538  '2538'
             2556  POP_BLOCK        
             2558  JUMP_FORWARD       3526  'to 3526'
           2560_0  COME_FROM_EXCEPT   2476  '2476'

 L. 742      2560  POP_TOP          
             2562  POP_TOP          
             2564  POP_TOP          

 L. 743      2566  LOAD_GLOBAL              print
             2568  LOAD_STR                 'cmd-12 parse failure!'
             2570  CALL_FUNCTION_1       1  '1 positional argument'
             2572  POP_TOP          

 L. 744      2574  POP_EXCEPT       
             2576  JUMP_FORWARD       3526  'to 3526'
             2578  END_FINALLY      
         2580_2582  JUMP_FORWARD       3526  'to 3526'
           2584_0  COME_FROM          2452  '2452'

 L. 746      2584  LOAD_FAST                'cmd_function'
             2586  LOAD_STR                 '13'
             2588  COMPARE_OP               ==
         2590_2592  POP_JUMP_IF_FALSE  2752  'to 2752'

 L. 747      2594  LOAD_GLOBAL              re
             2596  LOAD_METHOD              compile
             2598  LOAD_STR                 '^\\$13,X(?P<X_displacement>[^ ]*),Y(?P<Y_displacement>[^ ]*),Z(?P<Z_displacement>[^ ]*)#'
             2600  CALL_METHOD_1         1  '1 positional argument'
             2602  STORE_FAST               'reg'

 L. 748      2604  LOAD_FAST                'reg'
             2606  LOAD_METHOD              match
             2608  LOAD_FAST                'cmd'
             2610  CALL_METHOD_1         1  '1 positional argument'
             2612  STORE_FAST               'regMatch'

 L. 749      2614  SETUP_EXCEPT       2728  'to 2728'

 L. 750      2616  LOAD_FAST                'regMatch'
             2618  LOAD_CONST               None
             2620  COMPARE_OP               !=
         2622_2624  POP_JUMP_IF_FALSE  2716  'to 2716'

 L. 751      2626  LOAD_GLOBAL              pygame
             2628  LOAD_ATTR                mixer
             2630  LOAD_METHOD              init
             2632  CALL_METHOD_0         0  '0 positional arguments'
             2634  POP_TOP          

 L. 752      2636  LOAD_GLOBAL              pygame
             2638  LOAD_ATTR                mixer
             2640  LOAD_ATTR                music
             2642  LOAD_METHOD              load
             2644  LOAD_STR                 '/home/pi/yahboom-raspblock/stabilizeStart.mp3'
             2646  CALL_METHOD_1         1  '1 positional argument'
             2648  POP_TOP          

 L. 753      2650  LOAD_GLOBAL              pygame
             2652  LOAD_ATTR                mixer
             2654  LOAD_ATTR                music
             2656  LOAD_METHOD              play
             2658  CALL_METHOD_0         0  '0 positional arguments'
             2660  POP_TOP          

 L. 754      2662  LOAD_FAST                'regMatch'
             2664  LOAD_METHOD              groupdict
             2666  CALL_METHOD_0         0  '0 positional arguments'
             2668  STORE_FAST               'linebits'

 L. 755      2670  LOAD_GLOBAL              int
             2672  LOAD_FAST                'linebits'
             2674  LOAD_STR                 'X_displacement'
             2676  BINARY_SUBSCR    
             2678  CALL_FUNCTION_1       1  '1 positional argument'
             2680  STORE_GLOBAL             Position_disp_X

 L. 756      2682  LOAD_GLOBAL              int
             2684  LOAD_FAST                'linebits'
             2686  LOAD_STR                 'Y_displacement'
             2688  BINARY_SUBSCR    
             2690  CALL_FUNCTION_1       1  '1 positional argument'
             2692  STORE_GLOBAL             Position_disp_Y

 L. 757      2694  LOAD_GLOBAL              int
             2696  LOAD_FAST                'linebits'
             2698  LOAD_STR                 'Z_displacement'
             2700  BINARY_SUBSCR    
             2702  CALL_FUNCTION_1       1  '1 positional argument'
             2704  STORE_GLOBAL             Position_disp_Z

 L. 758      2706  LOAD_STR                 'position'
             2708  STORE_GLOBAL             g_presentation_mode

 L. 759      2710  LOAD_CONST               1
             2712  STORE_GLOBAL             g_Position_update
             2714  JUMP_FORWARD       2724  'to 2724'
           2716_0  COME_FROM          2622  '2622'

 L. 761      2716  LOAD_GLOBAL              print
             2718  LOAD_STR                 'cmd-13 expression parse failure!'
             2720  CALL_FUNCTION_1       1  '1 positional argument'
             2722  POP_TOP          
           2724_0  COME_FROM          2714  '2714'
             2724  POP_BLOCK        
             2726  JUMP_FORWARD       3526  'to 3526'
           2728_0  COME_FROM_EXCEPT   2614  '2614'

 L. 762      2728  POP_TOP          
             2730  POP_TOP          
             2732  POP_TOP          

 L. 763      2734  LOAD_GLOBAL              print
             2736  LOAD_STR                 'cmd-13 parse failure!'
             2738  CALL_FUNCTION_1       1  '1 positional argument'
             2740  POP_TOP          

 L. 764      2742  POP_EXCEPT       
             2744  JUMP_FORWARD       3526  'to 3526'
             2746  END_FINALLY      
         2748_2750  JUMP_FORWARD       3526  'to 3526'
           2752_0  COME_FROM          2590  '2590'

 L. 766      2752  LOAD_FAST                'cmd_function'
             2754  LOAD_STR                 '14'
             2756  COMPARE_OP               ==
         2758_2760  POP_JUMP_IF_FALSE  3108  'to 3108'

 L. 767      2762  LOAD_GLOBAL              re
             2764  LOAD_METHOD              compile
             2766  LOAD_STR                 '^\\$14,(?P<mode_select>[^ ]*)#'
             2768  CALL_METHOD_1         1  '1 positional argument'
             2770  STORE_FAST               'reg'

 L. 768      2772  LOAD_FAST                'reg'
             2774  LOAD_METHOD              match
             2776  LOAD_FAST                'cmd'
             2778  CALL_METHOD_1         1  '1 positional argument'
             2780  STORE_FAST               'regMatch'

 L. 769  2782_2784  SETUP_EXCEPT       3084  'to 3084'

 L. 770      2786  LOAD_FAST                'regMatch'
             2788  LOAD_CONST               None
             2790  COMPARE_OP               !=
         2792_2794  POP_JUMP_IF_FALSE  3072  'to 3072'

 L. 771      2796  LOAD_FAST                'regMatch'
             2798  LOAD_METHOD              groupdict
             2800  CALL_METHOD_0         0  '0 positional arguments'
             2802  STORE_FAST               'linebits'

 L. 772      2804  LOAD_FAST                'linebits'
             2806  LOAD_STR                 'mode_select'
             2808  BINARY_SUBSCR    
             2810  STORE_FAST               'mode_select'

 L. 773      2812  LOAD_FAST                'mode_select'
             2814  LOAD_STR                 '0'
             2816  COMPARE_OP               ==
         2818_2820  POP_JUMP_IF_FALSE  2916  'to 2916'

 L. 774      2822  LOAD_STR                 '0'
             2824  STORE_GLOBAL             g_mode

 L. 776      2826  LOAD_STR                 '0'
             2828  STORE_GLOBAL             g_servormode

 L. 777      2830  LOAD_STR                 'Free'
             2832  STORE_GLOBAL             g_robot_motion_mode

 L. 778      2834  LOAD_STR                 'unlock'
             2836  STORE_GLOBAL             g_z_state

 L. 779      2838  LOAD_STR                 '0'
             2840  STORE_GLOBAL             g_presentation_mode

 L. 780      2842  LOAD_STR                 '0'
             2844  STORE_GLOBAL             g_target_mode

 L. 781      2846  LOAD_STR                 'qrcode'
             2848  STORE_GLOBAL             g_tag_select

 L. 782      2850  LOAD_STR                 'close'
             2852  STORE_GLOBAL             g_tag_identify_switch

 L. 783      2854  LOAD_STR                 'close'
             2856  STORE_GLOBAL             g_tag_brodcast_switch

 L. 784      2858  LOAD_STR                 ''
             2860  STORE_FAST               'identify_tag'

 L. 785      2862  LOAD_STR                 ''
             2864  STORE_FAST               'last_identify_tag'

 L. 786      2866  LOAD_STR                 'close'
             2868  STORE_GLOBAL             g_auto_drive_switch

 L. 787      2870  LOAD_CONST               0
             2872  STORE_GLOBAL             g_drive_view_switch

 L. 789      2874  LOAD_CONST               0
             2876  DUP_TOP          
             2878  STORE_GLOBAL             Speed_axis_X
             2880  DUP_TOP          
             2882  STORE_GLOBAL             Speed_axis_Y
             2884  STORE_GLOBAL             Speed_axis_Z

 L. 790      2886  LOAD_CONST               0
             2888  DUP_TOP          
             2890  STORE_GLOBAL             Speed_WheelA
             2892  DUP_TOP          
             2894  STORE_GLOBAL             Speed_WheelB
             2896  DUP_TOP          
             2898  STORE_GLOBAL             Speed_WheelC
             2900  STORE_GLOBAL             Speed_WheelD

 L. 791      2902  LOAD_CONST               0
             2904  DUP_TOP          
             2906  STORE_GLOBAL             Position_disp_X
             2908  DUP_TOP          
             2910  STORE_GLOBAL             Position_disp_Y
             2912  STORE_GLOBAL             Position_disp_Z
             2914  JUMP_FORWARD       3070  'to 3070'
           2916_0  COME_FROM          2818  '2818'

 L. 793      2916  LOAD_FAST                'mode_select'
             2918  LOAD_STR                 '1'
             2920  COMPARE_OP               ==
         2922_2924  POP_JUMP_IF_FALSE  2936  'to 2936'

 L. 794      2926  LOAD_STR                 'remote_control'
             2928  STORE_GLOBAL             g_mode

 L. 795      2930  LOAD_STR                 'Free'
             2932  STORE_GLOBAL             g_robot_motion_mode
             2934  JUMP_FORWARD       3070  'to 3070'
           2936_0  COME_FROM          2922  '2922'

 L. 796      2936  LOAD_FAST                'mode_select'
             2938  LOAD_STR                 '2'
             2940  COMPARE_OP               ==
         2942_2944  POP_JUMP_IF_FALSE  2952  'to 2952'

 L. 797      2946  LOAD_STR                 'mecanum_control'
             2948  STORE_GLOBAL             g_mode
             2950  JUMP_FORWARD       3070  'to 3070'
           2952_0  COME_FROM          2942  '2942'

 L. 798      2952  LOAD_FAST                'mode_select'
             2954  LOAD_STR                 '3'
             2956  COMPARE_OP               ==
         2958_2960  POP_JUMP_IF_FALSE  2968  'to 2968'

 L. 799      2962  LOAD_STR                 'presentation'
             2964  STORE_GLOBAL             g_mode
             2966  JUMP_FORWARD       3070  'to 3070'
           2968_0  COME_FROM          2958  '2958'

 L. 800      2968  LOAD_FAST                'mode_select'
             2970  LOAD_STR                 '4'
             2972  COMPARE_OP               ==
         2974_2976  POP_JUMP_IF_FALSE  3004  'to 3004'

 L. 801      2978  LOAD_STR                 'target_track'
             2980  STORE_GLOBAL             g_mode

 L. 802      2982  LOAD_CONST               1500
             2984  DUP_TOP          
             2986  STORE_FAST               'target_valuex'
             2988  STORE_FAST               'target_valuey'

 L. 803      2990  LOAD_GLOBAL              robot
             2992  LOAD_METHOD              Servo_control
             2994  LOAD_FAST                'target_valuex'
             2996  LOAD_FAST                'target_valuey'
             2998  CALL_METHOD_2         2  '2 positional arguments'
             3000  POP_TOP          
             3002  JUMP_FORWARD       3070  'to 3070'
           3004_0  COME_FROM          2974  '2974'

 L. 804      3004  LOAD_FAST                'mode_select'
             3006  LOAD_STR                 '5'
             3008  COMPARE_OP               ==
         3010_3012  POP_JUMP_IF_FALSE  3040  'to 3040'

 L. 805      3014  LOAD_STR                 'tag_identification'
             3016  STORE_GLOBAL             g_mode

 L. 806      3018  LOAD_CONST               1500
             3020  DUP_TOP          
             3022  STORE_FAST               'target_valuex'
             3024  STORE_FAST               'target_valuey'

 L. 807      3026  LOAD_GLOBAL              robot
             3028  LOAD_METHOD              Servo_control
             3030  LOAD_FAST                'target_valuex'
             3032  LOAD_FAST                'target_valuey'
             3034  CALL_METHOD_2         2  '2 positional arguments'
             3036  POP_TOP          
             3038  JUMP_FORWARD       3070  'to 3070'
           3040_0  COME_FROM          3010  '3010'

 L. 808      3040  LOAD_FAST                'mode_select'
             3042  LOAD_STR                 '6'
             3044  COMPARE_OP               ==
         3046_3048  POP_JUMP_IF_FALSE  3056  'to 3056'

 L. 809      3050  LOAD_STR                 'voice_broadcast'
             3052  STORE_GLOBAL             g_mode
             3054  JUMP_FORWARD       3070  'to 3070'
           3056_0  COME_FROM          3046  '3046'

 L. 810      3056  LOAD_FAST                'mode_select'
             3058  LOAD_STR                 '7'
             3060  COMPARE_OP               ==
         3062_3064  POP_JUMP_IF_FALSE  3080  'to 3080'

 L. 811      3066  LOAD_STR                 'auto_drive'
             3068  STORE_GLOBAL             g_mode
           3070_0  COME_FROM          3054  '3054'
           3070_1  COME_FROM          3038  '3038'
           3070_2  COME_FROM          3002  '3002'
           3070_3  COME_FROM          2966  '2966'
           3070_4  COME_FROM          2950  '2950'
           3070_5  COME_FROM          2934  '2934'
           3070_6  COME_FROM          2914  '2914'
             3070  JUMP_FORWARD       3080  'to 3080'
           3072_0  COME_FROM          2792  '2792'

 L. 813      3072  LOAD_GLOBAL              print
             3074  LOAD_STR                 'cmd-14 expression parse failure!'
             3076  CALL_FUNCTION_1       1  '1 positional argument'
             3078  POP_TOP          
           3080_0  COME_FROM          3070  '3070'
           3080_1  COME_FROM          3062  '3062'
             3080  POP_BLOCK        
             3082  JUMP_FORWARD       3526  'to 3526'
           3084_0  COME_FROM_EXCEPT   2782  '2782'

 L. 814      3084  POP_TOP          
             3086  POP_TOP          
             3088  POP_TOP          

 L. 815      3090  LOAD_GLOBAL              print
             3092  LOAD_STR                 'cmd-14 parse failure!'
             3094  CALL_FUNCTION_1       1  '1 positional argument'
             3096  POP_TOP          

 L. 816      3098  POP_EXCEPT       
             3100  JUMP_FORWARD       3526  'to 3526'
             3102  END_FINALLY      
         3104_3106  JUMP_FORWARD       3526  'to 3526'
           3108_0  COME_FROM          2758  '2758'

 L. 818      3108  LOAD_FAST                'cmd_function'
             3110  LOAD_STR                 '15'
             3112  COMPARE_OP               ==
         3114_3116  POP_JUMP_IF_FALSE  3234  'to 3234'

 L. 819      3118  LOAD_GLOBAL              re
             3120  LOAD_METHOD              compile
             3122  LOAD_STR                 '^\\$15,(?P<Remote_mode>[^ ]*)#'
             3124  CALL_METHOD_1         1  '1 positional argument'
             3126  STORE_FAST               'reg'

 L. 820      3128  LOAD_FAST                'reg'
             3130  LOAD_METHOD              match
             3132  LOAD_FAST                'cmd'
             3134  CALL_METHOD_1         1  '1 positional argument'
             3136  STORE_FAST               'regMatch'

 L. 821      3138  SETUP_EXCEPT       3210  'to 3210'

 L. 822      3140  LOAD_FAST                'regMatch'
             3142  LOAD_CONST               None
             3144  COMPARE_OP               !=
         3146_3148  POP_JUMP_IF_FALSE  3198  'to 3198'

 L. 823      3150  LOAD_FAST                'regMatch'
             3152  LOAD_METHOD              groupdict
             3154  CALL_METHOD_0         0  '0 positional arguments'
             3156  STORE_FAST               'linebits'

 L. 824      3158  LOAD_FAST                'linebits'
             3160  LOAD_STR                 'Remote_mode'
             3162  BINARY_SUBSCR    
             3164  STORE_FAST               'Remote_mode'

 L. 825      3166  LOAD_FAST                'Remote_mode'
             3168  LOAD_STR                 '0'
             3170  COMPARE_OP               ==
         3172_3174  POP_JUMP_IF_FALSE  3182  'to 3182'

 L. 826      3176  LOAD_STR                 'Free'
             3178  STORE_GLOBAL             g_robot_motion_mode
             3180  JUMP_FORWARD       3196  'to 3196'
           3182_0  COME_FROM          3172  '3172'

 L. 827      3182  LOAD_FAST                'Remote_mode'
             3184  LOAD_STR                 '1'
             3186  COMPARE_OP               ==
         3188_3190  POP_JUMP_IF_FALSE  3206  'to 3206'

 L. 828      3192  LOAD_STR                 'Stabilize'
             3194  STORE_GLOBAL             g_robot_motion_mode
           3196_0  COME_FROM          3180  '3180'
             3196  JUMP_FORWARD       3206  'to 3206'
           3198_0  COME_FROM          3146  '3146'

 L. 830      3198  LOAD_GLOBAL              print
             3200  LOAD_STR                 'cmd-15 expression parse failure!'
             3202  CALL_FUNCTION_1       1  '1 positional argument'
             3204  POP_TOP          
           3206_0  COME_FROM          3196  '3196'
           3206_1  COME_FROM          3188  '3188'
             3206  POP_BLOCK        
             3208  JUMP_FORWARD       3526  'to 3526'
           3210_0  COME_FROM_EXCEPT   3138  '3138'

 L. 831      3210  POP_TOP          
             3212  POP_TOP          
             3214  POP_TOP          

 L. 832      3216  LOAD_GLOBAL              print
             3218  LOAD_STR                 'cmd-15 parse failure!'
             3220  CALL_FUNCTION_1       1  '1 positional argument'
             3222  POP_TOP          

 L. 833      3224  POP_EXCEPT       
             3226  JUMP_FORWARD       3526  'to 3526'
             3228  END_FINALLY      
         3230_3232  JUMP_FORWARD       3526  'to 3526'
           3234_0  COME_FROM          3114  '3114'

 L. 835      3234  LOAD_FAST                'cmd_function'
             3236  LOAD_STR                 '16'
             3238  COMPARE_OP               ==
         3240_3242  POP_JUMP_IF_FALSE  3396  'to 3396'

 L. 836      3244  LOAD_GLOBAL              re
             3246  LOAD_METHOD              compile
             3248  LOAD_STR                 '^\\$16,\\((?P<X_value>[^ ]*),(?P<Y_value>[^ ]*)\\),(?P<meanshint_switch>[^ ]*)#'
             3250  CALL_METHOD_1         1  '1 positional argument'
             3252  STORE_FAST               'reg'

 L. 837      3254  LOAD_FAST                'reg'
             3256  LOAD_METHOD              match
             3258  LOAD_FAST                'cmd'
             3260  CALL_METHOD_1         1  '1 positional argument'
             3262  STORE_FAST               'regMatch'

 L. 838      3264  SETUP_EXCEPT       3374  'to 3374'

 L. 839      3266  LOAD_FAST                'regMatch'
             3268  LOAD_CONST               None
             3270  COMPARE_OP               !=
         3272_3274  POP_JUMP_IF_FALSE  3362  'to 3362'

 L. 840      3276  LOAD_FAST                'regMatch'
             3278  LOAD_METHOD              groupdict
             3280  CALL_METHOD_0         0  '0 positional arguments'
             3282  STORE_FAST               'linebits'

 L. 841      3284  LOAD_FAST                'linebits'
             3286  LOAD_STR                 'meanshint_switch'
             3288  BINARY_SUBSCR    
             3290  STORE_FAST               'meanshint_switch'

 L. 842      3292  LOAD_FAST                'meanshint_switch'
             3294  LOAD_STR                 '1'
             3296  COMPARE_OP               ==
         3298_3300  POP_JUMP_IF_FALSE  3336  'to 3336'

 L. 843      3302  LOAD_GLOBAL              int
             3304  LOAD_FAST                'linebits'
             3306  LOAD_STR                 'X_value'
             3308  BINARY_SUBSCR    
             3310  CALL_FUNCTION_1       1  '1 positional argument'
             3312  STORE_GLOBAL             meanshift_X

 L. 844      3314  LOAD_GLOBAL              int
             3316  LOAD_FAST                'linebits'
             3318  LOAD_STR                 'Y_value'
             3320  BINARY_SUBSCR    
             3322  CALL_FUNCTION_1       1  '1 positional argument'
             3324  STORE_GLOBAL             meanshift_Y

 L. 845      3326  LOAD_CONST               1
             3328  STORE_GLOBAL             meanshift_update_flag

 L. 846      3330  LOAD_STR                 'meanshift_track'
             3332  STORE_GLOBAL             g_target_mode
             3334  JUMP_FORWARD       3360  'to 3360'
           3336_0  COME_FROM          3298  '3298'

 L. 847      3336  LOAD_FAST                'meanshint_switch'
             3338  LOAD_STR                 '0'
             3340  COMPARE_OP               ==
         3342_3344  POP_JUMP_IF_FALSE  3370  'to 3370'

 L. 848      3346  LOAD_GLOBAL              g_target_mode
             3348  LOAD_STR                 'meanshift_track'
             3350  COMPARE_OP               ==
         3352_3354  POP_JUMP_IF_FALSE  3370  'to 3370'

 L. 849      3356  LOAD_STR                 '0'
             3358  STORE_GLOBAL             g_target_mode
           3360_0  COME_FROM          3334  '3334'
             3360  JUMP_FORWARD       3370  'to 3370'
           3362_0  COME_FROM          3272  '3272'

 L. 852      3362  LOAD_GLOBAL              print
             3364  LOAD_STR                 'cmd-16 expression parse failure!'
             3366  CALL_FUNCTION_1       1  '1 positional argument'
             3368  POP_TOP          
           3370_0  COME_FROM          3360  '3360'
           3370_1  COME_FROM          3352  '3352'
           3370_2  COME_FROM          3342  '3342'
             3370  POP_BLOCK        
             3372  JUMP_FORWARD       3394  'to 3394'
           3374_0  COME_FROM_EXCEPT   3264  '3264'

 L. 853      3374  POP_TOP          
             3376  POP_TOP          
             3378  POP_TOP          

 L. 854      3380  LOAD_GLOBAL              print
             3382  LOAD_STR                 'cmd-16 parse failure!'
             3384  CALL_FUNCTION_1       1  '1 positional argument'
             3386  POP_TOP          

 L. 855      3388  POP_EXCEPT       
             3390  JUMP_FORWARD       3394  'to 3394'
             3392  END_FINALLY      
           3394_0  COME_FROM          3390  '3390'
           3394_1  COME_FROM          3372  '3372'
             3394  JUMP_FORWARD       3526  'to 3526'
           3396_0  COME_FROM          3240  '3240'

 L. 857      3396  LOAD_FAST                'cmd_function'
             3398  LOAD_STR                 '17'
             3400  COMPARE_OP               ==
         3402_3404  POP_JUMP_IF_FALSE  3526  'to 3526'

 L. 858      3406  LOAD_GLOBAL              re
             3408  LOAD_METHOD              compile
             3410  LOAD_STR                 '^\\$17,(?P<view_switch>[^ ]*)#'
             3412  CALL_METHOD_1         1  '1 positional argument'
             3414  STORE_FAST               'reg'

 L. 859      3416  LOAD_FAST                'reg'
             3418  LOAD_METHOD              match
             3420  LOAD_FAST                'cmd'
             3422  CALL_METHOD_1         1  '1 positional argument'
             3424  STORE_FAST               'regMatch'

 L. 860      3426  SETUP_EXCEPT       3506  'to 3506'

 L. 861      3428  LOAD_FAST                'regMatch'
             3430  LOAD_CONST               None
             3432  COMPARE_OP               !=
         3434_3436  POP_JUMP_IF_FALSE  3494  'to 3494'

 L. 862      3438  LOAD_FAST                'regMatch'
             3440  LOAD_METHOD              groupdict
             3442  CALL_METHOD_0         0  '0 positional arguments'
             3444  STORE_FAST               'linebits'

 L. 863      3446  LOAD_FAST                'linebits'
             3448  LOAD_STR                 'view_switch'
             3450  BINARY_SUBSCR    
             3452  STORE_FAST               'view_switch'

 L. 864      3454  LOAD_FAST                'view_switch'
             3456  LOAD_STR                 '1'
             3458  COMPARE_OP               ==
         3460_3462  POP_JUMP_IF_FALSE  3502  'to 3502'

 L. 865      3464  LOAD_GLOBAL              g_drive_view_switch
             3466  LOAD_CONST               1
             3468  BINARY_ADD       
             3470  LOAD_CONST               2
             3472  COMPARE_OP               >
         3474_3476  POP_JUMP_IF_FALSE  3484  'to 3484'

 L. 866      3478  LOAD_CONST               0
             3480  STORE_GLOBAL             g_drive_view_switch
             3482  JUMP_FORWARD       3492  'to 3492'
           3484_0  COME_FROM          3474  '3474'

 L. 868      3484  LOAD_GLOBAL              g_drive_view_switch
             3486  LOAD_CONST               1
             3488  INPLACE_ADD      
             3490  STORE_GLOBAL             g_drive_view_switch
           3492_0  COME_FROM          3482  '3482'
             3492  JUMP_FORWARD       3502  'to 3502'
           3494_0  COME_FROM          3434  '3434'

 L. 870      3494  LOAD_GLOBAL              print
             3496  LOAD_STR                 'cmd-17 expression parse failure!'
             3498  CALL_FUNCTION_1       1  '1 positional argument'
             3500  POP_TOP          
           3502_0  COME_FROM          3492  '3492'
           3502_1  COME_FROM          3460  '3460'
           3502_2  COME_FROM          3208  '3208'
           3502_3  COME_FROM          3082  '3082'
           3502_4  COME_FROM          2726  '2726'
           3502_5  COME_FROM          2558  '2558'
           3502_6  COME_FROM          2420  '2420'
           3502_7  COME_FROM          2230  '2230'
           3502_8  COME_FROM          2092  '2092'
           3502_9  COME_FROM          1956  '1956'
          3502_10  COME_FROM          1778  '1778'
          3502_11  COME_FROM          1476  '1476'
          3502_12  COME_FROM          1036  '1036'
          3502_13  COME_FROM           450  '450'
          3502_14  COME_FROM           260  '260'
          3502_15  COME_FROM           112  '112'
             3502  POP_BLOCK        
             3504  JUMP_FORWARD       3526  'to 3526'
           3506_0  COME_FROM_EXCEPT   3426  '3426'

 L. 871      3506  POP_TOP          
             3508  POP_TOP          
             3510  POP_TOP          

 L. 872      3512  LOAD_GLOBAL              print
           3514_0  COME_FROM          1250  '1250'
             3514  LOAD_STR                 'cmd-17 parse failure!'
             3516  CALL_FUNCTION_1       1  '1 positional argument'
             3518  POP_TOP          
           3520_0  COME_FROM          3226  '3226'
           3520_1  COME_FROM          3100  '3100'
           3520_2  COME_FROM          2744  '2744'
           3520_3  COME_FROM          2576  '2576'
           3520_4  COME_FROM          2438  '2438'
           3520_5  COME_FROM          2248  '2248'
           3520_6  COME_FROM          2110  '2110'
           3520_7  COME_FROM          1974  '1974'
           3520_8  COME_FROM          1796  '1796'
           3520_9  COME_FROM          1494  '1494'
          3520_10  COME_FROM          1054  '1054'
          3520_11  COME_FROM           468  '468'
          3520_12  COME_FROM           278  '278'
          3520_13  COME_FROM           130  '130'

 L. 873      3520  POP_EXCEPT       
             3522  JUMP_FORWARD       3526  'to 3526'
             3524  END_FINALLY      
           3526_0  COME_FROM          3522  '3522'
           3526_1  COME_FROM          3504  '3504'
           3526_2  COME_FROM          3402  '3402'
           3526_3  COME_FROM          3394  '3394'
           3526_4  COME_FROM          3230  '3230'
           3526_5  COME_FROM          3104  '3104'
           3526_6  COME_FROM          2748  '2748'
           3526_7  COME_FROM          2580  '2580'
           3526_8  COME_FROM          2442  '2442'
           3526_9  COME_FROM          2252  '2252'
          3526_10  COME_FROM          2114  '2114'
          3526_11  COME_FROM          1978  '1978'
          3526_12  COME_FROM          1800  '1800'
          3526_13  COME_FROM          1498  '1498'
          3526_14  COME_FROM          1260  '1260'
          3526_15  COME_FROM          1058  '1058'
          3526_16  COME_FROM           472  '472'
          3526_17  COME_FROM           282  '282'
          3526_18  COME_FROM           134  '134'

Parse error at or near `POP_BLOCK' instruction at offset 3502


ser = serial.Serial('/dev/ttyAMA0', 115200)
ser.flushInput()

def Attitude_update():
    count = ser.inWaiting()
    if count != 0:
        recv = list(ser.read(count))
        recv = str((bytes(recv)), encoding='UTF-8')
        if recv.find('{A') != -1 and recv.find('}#') != -1:
            reg = re.compile('^{A(?P<Pitch>[^ ]*):(?P<Roll>[^ ]*):(?P<Yaw>[^ ]*):(?P<Voltage>[^ ]*)}#')
            regMatch = reg.match(recv)
            try:
                if regMatch != None:
                    linebits = regMatch.groupdict()
                    temp = '$01,' + str(float(linebits['Voltage']) / 100.0) + ',' + str(int(int(linebits['Roll']) / 100)) + ',' + str(int(int(linebits['Pitch']) / 100)) + ',' + str(int(int(linebits['Yaw']) / 100)) + ',#'
                    send_msg(g_socket, temp.encode('utf-8'))
            except:
                pass

    ser.flushInput()


def motion_refresh--- This code section failed: ---

 L. 907         0  LOAD_CONST               0
                2  STORE_FAST               'run_mode'

 L. 909         4  LOAD_CONST               0
                6  STORE_FAST               'delay_count'

 L. 910      8_10  SETUP_LOOP         1012  'to 1012'

 L. 911        12  LOAD_GLOBAL              g_mode
               14  LOAD_STR                 'presentation'
               16  COMPARE_OP               ==
               18  POP_JUMP_IF_FALSE    68  'to 68'
               20  LOAD_GLOBAL              g_presentation_mode
               22  LOAD_STR                 'position'
               24  COMPARE_OP               ==
               26  POP_JUMP_IF_FALSE    68  'to 68'

 L. 912        28  LOAD_FAST                'run_mode'
               30  LOAD_CONST               1
               32  COMPARE_OP               !=
               34  POP_JUMP_IF_FALSE   106  'to 106'

 L. 913        36  LOAD_GLOBAL              robot
               38  LOAD_METHOD              PID_Mode_control
               40  LOAD_CONST               1
               42  LOAD_CONST               200
               44  LOAD_CONST               150
               46  LOAD_CONST               20
               48  LOAD_CONST               0
               50  LOAD_CONST               20
               52  LOAD_CONST               12
               54  LOAD_CONST               2
               56  LOAD_CONST               5
               58  CALL_METHOD_9         9  '9 positional arguments'
               60  POP_TOP          

 L. 914        62  LOAD_CONST               1
               64  STORE_FAST               'run_mode'
               66  JUMP_FORWARD        106  'to 106'
             68_0  COME_FROM            26  '26'
             68_1  COME_FROM            18  '18'

 L. 916        68  LOAD_FAST                'run_mode'
               70  LOAD_CONST               0
               72  COMPARE_OP               !=
               74  POP_JUMP_IF_FALSE   106  'to 106'

 L. 917        76  LOAD_GLOBAL              robot
               78  LOAD_METHOD              PID_Mode_control
               80  LOAD_CONST               0
               82  LOAD_CONST               200
               84  LOAD_CONST               150
               86  LOAD_CONST               20
               88  LOAD_CONST               0
               90  LOAD_CONST               20
               92  LOAD_CONST               12
               94  LOAD_CONST               2
               96  LOAD_CONST               5
               98  CALL_METHOD_9         9  '9 positional arguments'
              100  POP_TOP          

 L. 918       102  LOAD_CONST               0
              104  STORE_FAST               'run_mode'
            106_0  COME_FROM            74  '74'
            106_1  COME_FROM            66  '66'
            106_2  COME_FROM            34  '34'

 L. 919       106  LOAD_GLOBAL              g_mode
              108  LOAD_STR                 'remote_control'
              110  COMPARE_OP               ==
              112  POP_JUMP_IF_TRUE    124  'to 124'
              114  LOAD_GLOBAL              g_mode
              116  LOAD_STR                 'mecanum_control'
              118  COMPARE_OP               ==
          120_122  POP_JUMP_IF_FALSE   386  'to 386'
            124_0  COME_FROM           112  '112'

 L. 920       124  LOAD_GLOBAL              Speed_axis_X
              126  LOAD_CONST               0
              128  COMPARE_OP               !=
              130  POP_JUMP_IF_TRUE    148  'to 148'
              132  LOAD_GLOBAL              Speed_axis_Y
              134  LOAD_CONST               0
              136  COMPARE_OP               !=
              138  POP_JUMP_IF_TRUE    148  'to 148'
              140  LOAD_GLOBAL              Speed_axis_Z
              142  LOAD_CONST               0
              144  COMPARE_OP               !=
              146  POP_JUMP_IF_FALSE   226  'to 226'
            148_0  COME_FROM           138  '138'
            148_1  COME_FROM           130  '130'

 L. 921       148  LOAD_GLOBAL              g_z_state
              150  LOAD_STR                 'unlock'
              152  COMPARE_OP               ==
              154  POP_JUMP_IF_FALSE   172  'to 172'

 L. 922       156  LOAD_GLOBAL              robot
              158  LOAD_METHOD              Speed_axis_control
              160  LOAD_GLOBAL              Speed_axis_X
              162  LOAD_GLOBAL              Speed_axis_Y
              164  LOAD_GLOBAL              Speed_axis_Z
              166  CALL_METHOD_3         3  '3 positional arguments'
              168  POP_TOP          
              170  JUMP_FORWARD        224  'to 224'
            172_0  COME_FROM           154  '154'

 L. 923       172  LOAD_GLOBAL              g_z_state
              174  LOAD_STR                 'lock'
              176  COMPARE_OP               ==
              178  POP_JUMP_IF_FALSE   224  'to 224'

 L. 924       180  LOAD_GLOBAL              g_robot_motion_mode
              182  LOAD_STR                 'Free'
              184  COMPARE_OP               ==
              186  POP_JUMP_IF_FALSE   204  'to 204'

 L. 925       188  LOAD_GLOBAL              robot
              190  LOAD_METHOD              Speed_axis_control
              192  LOAD_GLOBAL              Speed_axis_X
              194  LOAD_GLOBAL              Speed_axis_Y
              196  LOAD_GLOBAL              Speed_axis_Z
              198  CALL_METHOD_3         3  '3 positional arguments'
              200  POP_TOP          
              202  JUMP_FORWARD        224  'to 224'
            204_0  COME_FROM           186  '186'

 L. 926       204  LOAD_GLOBAL              g_robot_motion_mode
              206  LOAD_STR                 'Stabilize'
              208  COMPARE_OP               ==
              210  POP_JUMP_IF_FALSE   224  'to 224'

 L. 927       212  LOAD_GLOBAL              robot
              214  LOAD_METHOD              Speed_axis_Yawhold_control
              216  LOAD_GLOBAL              Speed_axis_X
              218  LOAD_GLOBAL              Speed_axis_Y
              220  CALL_METHOD_2         2  '2 positional arguments'
              222  POP_TOP          
            224_0  COME_FROM           210  '210'
            224_1  COME_FROM           202  '202'
            224_2  COME_FROM           178  '178'
            224_3  COME_FROM           170  '170'
              224  JUMP_FORWARD        282  'to 282'
            226_0  COME_FROM           146  '146'

 L. 928       226  LOAD_GLOBAL              Speed_WheelA
              228  LOAD_CONST               0
              230  COMPARE_OP               !=
          232_234  POP_JUMP_IF_TRUE    266  'to 266'
              236  LOAD_GLOBAL              Speed_WheelB
              238  LOAD_CONST               0
              240  COMPARE_OP               !=
          242_244  POP_JUMP_IF_TRUE    266  'to 266'
              246  LOAD_GLOBAL              Speed_WheelC
              248  LOAD_CONST               0
              250  COMPARE_OP               !=
          252_254  POP_JUMP_IF_TRUE    266  'to 266'
              256  LOAD_GLOBAL              Speed_WheelD
              258  LOAD_CONST               0
              260  COMPARE_OP               !=
          262_264  POP_JUMP_IF_FALSE   282  'to 282'
            266_0  COME_FROM           252  '252'
            266_1  COME_FROM           242  '242'
            266_2  COME_FROM           232  '232'

 L. 929       266  LOAD_GLOBAL              robot
              268  LOAD_METHOD              Speed_Wheel_control
              270  LOAD_GLOBAL              Speed_WheelA
              272  LOAD_GLOBAL              Speed_WheelB
              274  LOAD_GLOBAL              Speed_WheelC
              276  LOAD_GLOBAL              Speed_WheelD
              278  CALL_METHOD_4         4  '4 positional arguments'
              280  POP_TOP          
            282_0  COME_FROM           262  '262'
            282_1  COME_FROM           224  '224'

 L. 931       282  LOAD_GLOBAL              g_servormode
              284  LOAD_STR                 'servo_forward'
              286  COMPARE_OP               ==
          288_290  POP_JUMP_IF_FALSE   302  'to 302'

 L. 932       292  LOAD_GLOBAL              camUpFunction
              294  LOAD_CONST               3
              296  CALL_FUNCTION_1       1  '1 positional argument'
              298  POP_TOP          
              300  JUMP_FORWARD        970  'to 970'
            302_0  COME_FROM           288  '288'

 L. 933       302  LOAD_GLOBAL              g_servormode
              304  LOAD_STR                 'servo_down'
              306  COMPARE_OP               ==
          308_310  POP_JUMP_IF_FALSE   322  'to 322'

 L. 934       312  LOAD_GLOBAL              camDownFunction
              314  LOAD_CONST               3
              316  CALL_FUNCTION_1       1  '1 positional argument'
              318  POP_TOP          
              320  JUMP_FORWARD        970  'to 970'
            322_0  COME_FROM           308  '308'

 L. 935       322  LOAD_GLOBAL              g_servormode
              324  LOAD_STR                 'servo_left'
              326  COMPARE_OP               ==
          328_330  POP_JUMP_IF_FALSE   342  'to 342'

 L. 936       332  LOAD_GLOBAL              camLeftFunction
              334  LOAD_CONST               3
              336  CALL_FUNCTION_1       1  '1 positional argument'
              338  POP_TOP          
              340  JUMP_FORWARD        970  'to 970'
            342_0  COME_FROM           328  '328'

 L. 937       342  LOAD_GLOBAL              g_servormode
              344  LOAD_STR                 'servo_right'
              346  COMPARE_OP               ==
          348_350  POP_JUMP_IF_FALSE   362  'to 362'

 L. 938       352  LOAD_GLOBAL              camRightFunction
              354  LOAD_CONST               3
              356  CALL_FUNCTION_1       1  '1 positional argument'
              358  POP_TOP          
              360  JUMP_FORWARD        970  'to 970'
            362_0  COME_FROM           348  '348'

 L. 939       362  LOAD_GLOBAL              g_servormode
              364  LOAD_STR                 'servo_init'
              366  COMPARE_OP               ==
          368_370  POP_JUMP_IF_FALSE   970  'to 970'

 L. 940       372  LOAD_STR                 '0'
              374  STORE_GLOBAL             g_servormode

 L. 941       376  LOAD_GLOBAL              camservoInitFunction
              378  CALL_FUNCTION_0       0  '0 positional arguments'
              380  POP_TOP          
          382_384  JUMP_FORWARD        970  'to 970'
            386_0  COME_FROM           120  '120'

 L. 942       386  LOAD_GLOBAL              g_mode
              388  LOAD_STR                 'presentation'
              390  COMPARE_OP               ==
          392_394  POP_JUMP_IF_FALSE   848  'to 848'

 L. 944       396  LOAD_GLOBAL              g_presentation_mode
              398  LOAD_STR                 'around'
              400  COMPARE_OP               ==
          402_404  POP_JUMP_IF_FALSE   482  'to 482'

 L. 945       406  LOAD_GLOBAL              print
              408  LOAD_STR                 'around'
              410  CALL_FUNCTION_1       1  '1 positional argument'
              412  POP_TOP          

 L. 946       414  SETUP_LOOP          452  'to 452'
              416  LOAD_GLOBAL              range
              418  LOAD_CONST               1
              420  LOAD_CONST               2000
              422  CALL_FUNCTION_2       2  '2 positional arguments'
              424  GET_ITER         
              426  FOR_ITER            450  'to 450'
              428  STORE_FAST               'i'

 L. 947       430  LOAD_GLOBAL              robot
              432  LOAD_METHOD              Speed_Wheel_control
              434  LOAD_CONST               -5
              436  LOAD_CONST               20
              438  LOAD_CONST               -20
              440  LOAD_CONST               5
              442  CALL_METHOD_4         4  '4 positional arguments'
              444  POP_TOP          
          446_448  JUMP_BACK           426  'to 426'
              450  POP_BLOCK        
            452_0  COME_FROM_LOOP      414  '414'

 L. 949       452  LOAD_GLOBAL              robot
              454  LOAD_METHOD              Speed_Wheel_control
              456  LOAD_CONST               0
              458  LOAD_CONST               0
              460  LOAD_CONST               0
              462  LOAD_CONST               0
              464  CALL_METHOD_4         4  '4 positional arguments'
              466  POP_TOP          

 L. 950       468  LOAD_GLOBAL              time
              470  LOAD_METHOD              sleep
              472  LOAD_CONST               2
              474  CALL_METHOD_1         1  '1 positional argument'
              476  POP_TOP          
          478_480  JUMP_ABSOLUTE       970  'to 970'
            482_0  COME_FROM           402  '402'

 L. 952       482  LOAD_GLOBAL              g_presentation_mode
              484  LOAD_STR                 'translation'
              486  COMPARE_OP               ==
          488_490  POP_JUMP_IF_FALSE   784  'to 784'

 L. 953       492  LOAD_GLOBAL              print
              494  LOAD_STR                 'translation'
              496  CALL_FUNCTION_1       1  '1 positional argument'
              498  POP_TOP          

 L. 954       500  SETUP_LOOP          538  'to 538'
              502  LOAD_GLOBAL              range
              504  LOAD_CONST               1
              506  LOAD_CONST               1000
              508  CALL_FUNCTION_2       2  '2 positional arguments'
              510  GET_ITER         
              512  FOR_ITER            536  'to 536'
              514  STORE_FAST               'i'

 L. 955       516  LOAD_GLOBAL              robot
              518  LOAD_METHOD              Speed_Wheel_control
              520  LOAD_CONST               -8
              522  LOAD_CONST               8
              524  LOAD_CONST               -8
              526  LOAD_CONST               8
              528  CALL_METHOD_4         4  '4 positional arguments'
              530  POP_TOP          
          532_534  JUMP_BACK           512  'to 512'
              536  POP_BLOCK        
            538_0  COME_FROM_LOOP      500  '500'

 L. 956       538  LOAD_GLOBAL              robot
              540  LOAD_METHOD              Speed_Wheel_control
              542  LOAD_CONST               0
              544  LOAD_CONST               0
              546  LOAD_CONST               0
              548  LOAD_CONST               0
              550  CALL_METHOD_4         4  '4 positional arguments'
              552  POP_TOP          

 L. 957       554  LOAD_GLOBAL              time
              556  LOAD_METHOD              sleep
              558  LOAD_CONST               2
              560  CALL_METHOD_1         1  '1 positional argument'
              562  POP_TOP          

 L. 958       564  SETUP_LOOP          602  'to 602'
              566  LOAD_GLOBAL              range
              568  LOAD_CONST               1
              570  LOAD_CONST               1000
              572  CALL_FUNCTION_2       2  '2 positional arguments'
              574  GET_ITER         
              576  FOR_ITER            600  'to 600'
              578  STORE_FAST               'i'

 L. 959       580  LOAD_GLOBAL              robot
              582  LOAD_METHOD              Speed_Wheel_control
              584  LOAD_CONST               -8
              586  LOAD_CONST               -8
              588  LOAD_CONST               -8
              590  LOAD_CONST               -8
              592  CALL_METHOD_4         4  '4 positional arguments'
              594  POP_TOP          
          596_598  JUMP_BACK           576  'to 576'
              600  POP_BLOCK        
            602_0  COME_FROM_LOOP      564  '564'

 L. 960       602  LOAD_GLOBAL              robot
              604  LOAD_METHOD              Speed_Wheel_control
              606  LOAD_CONST               0
              608  LOAD_CONST               0
              610  LOAD_CONST               0
              612  LOAD_CONST               0
              614  CALL_METHOD_4         4  '4 positional arguments'
              616  POP_TOP          

 L. 961       618  LOAD_GLOBAL              time
              620  LOAD_METHOD              sleep
              622  LOAD_CONST               2
              624  CALL_METHOD_1         1  '1 positional argument'
              626  POP_TOP          

 L. 962       628  SETUP_LOOP          666  'to 666'
              630  LOAD_GLOBAL              range
              632  LOAD_CONST               1
              634  LOAD_CONST               1000
              636  CALL_FUNCTION_2       2  '2 positional arguments'
              638  GET_ITER         
              640  FOR_ITER            664  'to 664'
              642  STORE_FAST               'i'

 L. 963       644  LOAD_GLOBAL              robot
              646  LOAD_METHOD              Speed_Wheel_control
              648  LOAD_CONST               8
              650  LOAD_CONST               -8
              652  LOAD_CONST               8
              654  LOAD_CONST               -8
              656  CALL_METHOD_4         4  '4 positional arguments'
              658  POP_TOP          
          660_662  JUMP_BACK           640  'to 640'
              664  POP_BLOCK        
            666_0  COME_FROM_LOOP      628  '628'

 L. 964       666  LOAD_GLOBAL              robot
              668  LOAD_METHOD              Speed_Wheel_control
              670  LOAD_CONST               0
              672  LOAD_CONST               0
              674  LOAD_CONST               0
              676  LOAD_CONST               0
              678  CALL_METHOD_4         4  '4 positional arguments'
              680  POP_TOP          

 L. 965       682  LOAD_GLOBAL              time
              684  LOAD_METHOD              sleep
              686  LOAD_CONST               2
              688  CALL_METHOD_1         1  '1 positional argument'
              690  POP_TOP          

 L. 966       692  SETUP_LOOP          730  'to 730'
              694  LOAD_GLOBAL              range
              696  LOAD_CONST               1
              698  LOAD_CONST               1000
              700  CALL_FUNCTION_2       2  '2 positional arguments'
              702  GET_ITER         
              704  FOR_ITER            728  'to 728'
              706  STORE_FAST               'i'

 L. 967       708  LOAD_GLOBAL              robot
              710  LOAD_METHOD              Speed_Wheel_control
              712  LOAD_CONST               8
              714  LOAD_CONST               8
              716  LOAD_CONST               8
              718  LOAD_CONST               8
              720  CALL_METHOD_4         4  '4 positional arguments'
              722  POP_TOP          
          724_726  JUMP_BACK           704  'to 704'
              728  POP_BLOCK        
            730_0  COME_FROM_LOOP      692  '692'

 L. 968       730  LOAD_GLOBAL              robot
              732  LOAD_METHOD              Speed_Wheel_control
              734  LOAD_CONST               0
              736  LOAD_CONST               0
              738  LOAD_CONST               0
              740  LOAD_CONST               0
              742  CALL_METHOD_4         4  '4 positional arguments'
              744  POP_TOP          

 L. 969       746  LOAD_GLOBAL              time
              748  LOAD_METHOD              sleep
              750  LOAD_CONST               2
              752  CALL_METHOD_1         1  '1 positional argument'
              754  POP_TOP          

 L. 971       756  LOAD_GLOBAL              robot
              758  LOAD_METHOD              Speed_Wheel_control
              760  LOAD_CONST               0
              762  LOAD_CONST               0
              764  LOAD_CONST               0
              766  LOAD_CONST               0
              768  CALL_METHOD_4         4  '4 positional arguments'
              770  POP_TOP          

 L. 972       772  LOAD_GLOBAL              time
              774  LOAD_METHOD              sleep
              776  LOAD_CONST               5
              778  CALL_METHOD_1         1  '1 positional argument'
              780  POP_TOP          
              782  JUMP_FORWARD        846  'to 846'
            784_0  COME_FROM           488  '488'

 L. 973       784  LOAD_GLOBAL              g_presentation_mode
              786  LOAD_STR                 'stabilize'
              788  COMPARE_OP               ==
          790_792  POP_JUMP_IF_FALSE   808  'to 808'

 L. 974       794  LOAD_GLOBAL              robot
              796  LOAD_METHOD              Speed_axis_Yawhold_control
              798  LOAD_CONST               0
              800  LOAD_CONST               0
              802  CALL_METHOD_2         2  '2 positional arguments'
              804  POP_TOP          
              806  JUMP_FORWARD        846  'to 846'
            808_0  COME_FROM           790  '790'

 L. 975       808  LOAD_GLOBAL              g_presentation_mode
              810  LOAD_STR                 'position'
              812  COMPARE_OP               ==
          814_816  POP_JUMP_IF_FALSE   970  'to 970'

 L. 976       818  LOAD_GLOBAL              g_Position_update
              820  LOAD_CONST               1
              822  COMPARE_OP               ==
          824_826  POP_JUMP_IF_FALSE   970  'to 970'

 L. 977       828  LOAD_GLOBAL              robot
              830  LOAD_METHOD              Position_disp_control
              832  LOAD_GLOBAL              Position_disp_X
              834  LOAD_GLOBAL              Position_disp_Y
              836  LOAD_GLOBAL              Position_disp_Z
              838  CALL_METHOD_3         3  '3 positional arguments'
              840  POP_TOP          

 L. 978       842  LOAD_CONST               0
              844  STORE_GLOBAL             g_Position_update
            846_0  COME_FROM           806  '806'
            846_1  COME_FROM           782  '782'
              846  JUMP_FORWARD        970  'to 970'
            848_0  COME_FROM           392  '392'

 L. 979       848  LOAD_GLOBAL              g_mode
              850  LOAD_STR                 'auto_drive'
              852  COMPARE_OP               ==
          854_856  POP_JUMP_IF_FALSE   960  'to 960'

 L. 980       858  LOAD_GLOBAL              g_servormode
              860  LOAD_STR                 'servo_forward'
              862  COMPARE_OP               ==
          864_866  POP_JUMP_IF_FALSE   878  'to 878'

 L. 981       868  LOAD_GLOBAL              camUpFunction
              870  LOAD_CONST               1
              872  CALL_FUNCTION_1       1  '1 positional argument'
              874  POP_TOP          
              876  JUMP_FORWARD        958  'to 958'
            878_0  COME_FROM           864  '864'

 L. 982       878  LOAD_GLOBAL              g_servormode
              880  LOAD_STR                 'servo_down'
              882  COMPARE_OP               ==
          884_886  POP_JUMP_IF_FALSE   898  'to 898'

 L. 983       888  LOAD_GLOBAL              camDownFunction
              890  LOAD_CONST               1
              892  CALL_FUNCTION_1       1  '1 positional argument'
              894  POP_TOP          
              896  JUMP_FORWARD        958  'to 958'
            898_0  COME_FROM           884  '884'

 L. 984       898  LOAD_GLOBAL              g_servormode
              900  LOAD_STR                 'servo_left'
              902  COMPARE_OP               ==
          904_906  POP_JUMP_IF_FALSE   918  'to 918'

 L. 985       908  LOAD_GLOBAL              camLeftFunction
              910  LOAD_CONST               1
              912  CALL_FUNCTION_1       1  '1 positional argument'
              914  POP_TOP          
              916  JUMP_FORWARD        958  'to 958'
            918_0  COME_FROM           904  '904'

 L. 986       918  LOAD_GLOBAL              g_servormode
              920  LOAD_STR                 'servo_right'
              922  COMPARE_OP               ==
          924_926  POP_JUMP_IF_FALSE   938  'to 938'

 L. 987       928  LOAD_GLOBAL              camRightFunction
              930  LOAD_CONST               1
              932  CALL_FUNCTION_1       1  '1 positional argument'
              934  POP_TOP          
              936  JUMP_FORWARD        958  'to 958'
            938_0  COME_FROM           924  '924'

 L. 988       938  LOAD_GLOBAL              g_servormode
              940  LOAD_STR                 'servo_init'
              942  COMPARE_OP               ==
          944_946  POP_JUMP_IF_FALSE   970  'to 970'

 L. 989       948  LOAD_STR                 '0'
              950  STORE_GLOBAL             g_servormode

 L. 990       952  LOAD_GLOBAL              camservoInitFunction
              954  CALL_FUNCTION_0       0  '0 positional arguments'
              956  POP_TOP          
            958_0  COME_FROM           936  '936'
            958_1  COME_FROM           916  '916'
            958_2  COME_FROM           896  '896'
            958_3  COME_FROM           876  '876'
              958  JUMP_FORWARD        970  'to 970'
            960_0  COME_FROM           854  '854'

 L. 992       960  LOAD_GLOBAL              time
              962  LOAD_METHOD              sleep
              964  LOAD_CONST               0.01
              966  CALL_METHOD_1         1  '1 positional argument'
              968  POP_TOP          
            970_0  COME_FROM           958  '958'
            970_1  COME_FROM           944  '944'
            970_2  COME_FROM           846  '846'
            970_3  COME_FROM           824  '824'
            970_4  COME_FROM           814  '814'
            970_5  COME_FROM           382  '382'
            970_6  COME_FROM           368  '368'

 L. 993       970  LOAD_FAST                'delay_count'
              972  LOAD_CONST               1
              974  INPLACE_ADD      
              976  STORE_FAST               'delay_count'

 L. 994       978  LOAD_FAST                'delay_count'
              980  LOAD_CONST               10
              982  COMPARE_OP               >=
          984_986  POP_JUMP_IF_FALSE   998  'to 998'

 L. 995       988  LOAD_CONST               0
              990  STORE_FAST               'delay_count'

 L. 996       992  LOAD_GLOBAL              Attitude_update
              994  CALL_FUNCTION_0       0  '0 positional arguments'
              996  POP_TOP          
            998_0  COME_FROM           984  '984'

 L. 997       998  LOAD_GLOBAL              time
             1000  LOAD_METHOD              sleep
             1002  LOAD_CONST               0.01
             1004  CALL_METHOD_1         1  '1 positional argument'
             1006  POP_TOP          
             1008  JUMP_BACK            12  'to 12'
             1010  POP_BLOCK        
           1012_0  COME_FROM_LOOP        8  '8'

Parse error at or near `COME_FROM' instruction at offset 282_0


motion_refresh_id = threading.Thread(target=motion_refresh)
motion_refresh_id.setDaemon(True)
motion_refresh_id.start()
MODEL_NAME = '/home/pi/yahboom-raspblock/ssdlite_mobilenet_v2_coco_2018_05_09'
PATH_TO_CKPT = MODEL_NAME + '/frozen_inference_graph.pb'
PATH_TO_LABELS = '/home/pi/yahboom-raspblock/data/mscoco_label_map.pbtxt'
NUM_CLASSES = 90
IMAGE_SIZE = (12, 8)
fileAlreadyExists = os.path.isfile(PATH_TO_CKPT)
if not fileAlreadyExists:
    print('Model does not exsist !')
    exit
print('Loading Graph...')
detection_graph = tf.Graph()
with detection_graph.as_default():
    od_graph_def = tf.compat.v1.GraphDef()
    with tf.io.gfile.GFile(PATH_TO_CKPT, 'rb') as (fid):
        serialized_graph = fid.read()
        od_graph_def.ParseFromString(serialized_graph)
        tf.import_graph_def(od_graph_def, name='')
label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES, use_display_name=True)
category_index = label_map_util.create_category_index(categories)
print('Finish Load Graph..')

def gen(l, window_size):
    index = 0
    ans = 0
    times = 0
    while True:
        while index < window_size:
            ans += l[(times + index)]
            index += 1

        yield float(ans) / float(window_size)
        index = 0
        ans = 0
        times += 1


def mean_filter(signal, window_size):
    window_size = 8
    temp = gen(signal, window_size)
    filtered = []
    for i in range(len(signal) - window_size):
        filtered.append(next(temp))

    return filtered


def find_peak(filtered_signal, length_data, thre, peak_width):
    l = []
    for i in range(1, length_data - 1):
        if filtered_signal[(i - 1)] < filtered_signal[i]:
            if filtered_signal[i] > filtered_signal[(i + 1)]:
                if filtered_signal[i] > thre:
                    l.append(i)
        if filtered_signal[i] == filtered_signal[(i - 1)] and filtered_signal[i] > thre:
            l.append(i)

    CC = len(l)
    cou = 0
    for j in range(1, CC):
        if l[j] - l[(j - 1)] < peak_width:
            cou = cou + 1

    rcou = CC - cou
    return rcou


def bgr8_to_jpeg(value, quality=75):
    return bytes(cv2.imencode('.jpg', value)[1])


def mode_handle--- This code section failed: ---

 L.1084         0  LOAD_CONST               0
                2  DUP_TOP          
                4  STORE_GLOBAL             face_x
                6  DUP_TOP          
                8  STORE_GLOBAL             face_y
               10  DUP_TOP          
               12  STORE_GLOBAL             face_w
               14  STORE_GLOBAL             face_h

 L.1085        16  LOAD_CONST               0
               18  DUP_TOP          
               20  STORE_FAST               'color_x'
               22  DUP_TOP          
               24  STORE_FAST               'color_y'
               26  STORE_FAST               'color_radius'

 L.1087        28  LOAD_STR                 ''
               30  STORE_FAST               'identify_tag'

 L.1088        32  LOAD_STR                 ''
               34  STORE_FAST               'last_identify_tag'

 L.1089        36  LOAD_CONST               0
               38  STORE_FAST               'object_count'

 L.1090        40  LOAD_CONST               0
               42  STORE_FAST               'object_brodcast_delay'

 L.1091        44  LOAD_GLOBAL              time
               46  LOAD_METHOD              time
               48  CALL_METHOD_0         0  '0 positional arguments'
               50  STORE_FAST               't_start'

 L.1092        52  LOAD_CONST               0
               54  STORE_FAST               'fps'

 L.1094        56  LOAD_CONST               8
               58  STORE_FAST               'window_size'

 L.1095        60  LOAD_CONST               1300
               62  STORE_FAST               'thre'

 L.1096        64  LOAD_CONST               20
               66  STORE_FAST               'peak_width'

 L.1104        68  LOAD_GLOBAL              np
               70  LOAD_METHOD              float32
               72  LOAD_CONST               0
               74  LOAD_CONST               149
               76  BUILD_LIST_2          2 
               78  LOAD_CONST               310
               80  LOAD_CONST               149
               82  BUILD_LIST_2          2 
               84  LOAD_CONST               271
               86  LOAD_CONST               72
               88  BUILD_LIST_2          2 
               90  LOAD_CONST               43
               92  LOAD_CONST               72
               94  BUILD_LIST_2          2 
               96  BUILD_LIST_4          4 
               98  CALL_METHOD_1         1  '1 positional argument'
              100  STORE_FAST               'matSrc'

 L.1105       102  LOAD_GLOBAL              np
              104  LOAD_METHOD              float32
              106  LOAD_CONST               0
              108  LOAD_CONST               240
              110  BUILD_LIST_2          2 
              112  LOAD_CONST               310
              114  LOAD_CONST               240
              116  BUILD_LIST_2          2 
              118  LOAD_CONST               310
              120  LOAD_CONST               0
              122  BUILD_LIST_2          2 
              124  LOAD_CONST               0
              126  LOAD_CONST               0
              128  BUILD_LIST_2          2 
              130  BUILD_LIST_4          4 
              132  CALL_METHOD_1         1  '1 positional argument'
              134  STORE_FAST               'matDst'

 L.1108       136  LOAD_GLOBAL              cv2
              138  LOAD_METHOD              getPerspectiveTransform
              140  LOAD_FAST                'matSrc'
              142  LOAD_FAST                'matDst'
              144  CALL_METHOD_2         2  '2 positional arguments'
              146  STORE_FAST               'matAffine'

 L.1110       148  LOAD_GLOBAL              np
              150  LOAD_METHOD              array
              152  LOAD_CONST               0
              154  LOAD_CONST               149
              156  BUILD_LIST_2          2 
              158  LOAD_CONST               310
              160  LOAD_CONST               149
              162  BUILD_LIST_2          2 
              164  LOAD_CONST               271
              166  LOAD_CONST               72
              168  BUILD_LIST_2          2 
              170  LOAD_CONST               43
              172  LOAD_CONST               72
              174  BUILD_LIST_2          2 
              176  BUILD_LIST_4          4 
              178  LOAD_GLOBAL              np
              180  LOAD_ATTR                int32
              182  CALL_METHOD_2         2  '2 positional arguments'
              184  STORE_FAST               'pts'

 L.1113       186  LOAD_GLOBAL              cv2
              188  LOAD_METHOD              VideoCapture
              190  LOAD_CONST               0
              192  CALL_METHOD_1         1  '1 positional argument'
              194  STORE_FAST               'g_camera'

 L.1114       196  LOAD_FAST                'g_camera'
              198  LOAD_METHOD              set
              200  LOAD_CONST               3
              202  LOAD_CONST               320
              204  CALL_METHOD_2         2  '2 positional arguments'
              206  POP_TOP          

 L.1115       208  LOAD_FAST                'g_camera'
              210  LOAD_METHOD              set
              212  LOAD_CONST               4
              214  LOAD_CONST               240
              216  CALL_METHOD_2         2  '2 positional arguments'
              218  POP_TOP          

 L.1116       220  LOAD_FAST                'g_camera'
              222  LOAD_METHOD              set
              224  LOAD_CONST               5
              226  LOAD_CONST               120
              228  CALL_METHOD_2         2  '2 positional arguments'
              230  POP_TOP          

 L.1117       232  LOAD_FAST                'g_camera'
              234  LOAD_METHOD              set
              236  LOAD_GLOBAL              cv2
              238  LOAD_ATTR                CAP_PROP_FOURCC
              240  LOAD_GLOBAL              cv2
              242  LOAD_ATTR                VideoWriter
              244  LOAD_METHOD              fourcc
              246  LOAD_STR                 'M'
              248  LOAD_STR                 'J'
              250  LOAD_STR                 'P'
              252  LOAD_STR                 'G'
              254  CALL_METHOD_4         4  '4 positional arguments'
              256  CALL_METHOD_2         2  '2 positional arguments'
              258  POP_TOP          

 L.1118       260  LOAD_FAST                'g_camera'
              262  LOAD_METHOD              set
              264  LOAD_GLOBAL              cv2
              266  LOAD_ATTR                CAP_PROP_BRIGHTNESS
              268  LOAD_CONST               40
              270  CALL_METHOD_2         2  '2 positional arguments'
              272  POP_TOP          

 L.1119       274  LOAD_FAST                'g_camera'
              276  LOAD_METHOD              set
              278  LOAD_GLOBAL              cv2
              280  LOAD_ATTR                CAP_PROP_CONTRAST
              282  LOAD_CONST               50
              284  CALL_METHOD_2         2  '2 positional arguments'
              286  POP_TOP          

 L.1120       288  LOAD_FAST                'g_camera'
              290  LOAD_METHOD              set
              292  LOAD_GLOBAL              cv2
              294  LOAD_ATTR                CAP_PROP_EXPOSURE
              296  LOAD_CONST               156
              298  CALL_METHOD_2         2  '2 positional arguments'
              300  POP_TOP          

 L.1121       302  LOAD_FAST                'g_camera'
              304  LOAD_METHOD              read
              306  CALL_METHOD_0         0  '0 positional arguments'
              308  UNPACK_SEQUENCE_2     2 
              310  STORE_FAST               'retval'
              312  STORE_FAST               'frame'

 L.1122       314  LOAD_GLOBAL              cv2
              316  LOAD_METHOD              imencode
              318  LOAD_STR                 '.jpg'
              320  LOAD_FAST                'frame'
              322  CALL_METHOD_2         2  '2 positional arguments'
              324  LOAD_CONST               1
              326  BINARY_SUBSCR    
              328  STORE_FAST               'imgencode'

 L.1124       330  LOAD_GLOBAL              PID
              332  LOAD_METHOD              PositionalPID
              334  LOAD_CONST               1.1
              336  LOAD_CONST               0.2
              338  LOAD_CONST               0.8
              340  CALL_METHOD_3         3  '3 positional arguments'
              342  STORE_FAST               'xservo_pid'

 L.1125       344  LOAD_GLOBAL              PID
              346  LOAD_METHOD              PositionalPID
              348  LOAD_CONST               0.8
              350  LOAD_CONST               0.2
              352  LOAD_CONST               0.8
              354  CALL_METHOD_3         3  '3 positional arguments'
              356  STORE_FAST               'yservo_pid'

 L.1127       358  LOAD_GLOBAL              PID
              360  LOAD_METHOD              PositionalPID
              362  LOAD_CONST               0.7
              364  LOAD_CONST               0.0
              366  LOAD_CONST               1.8
              368  CALL_METHOD_3         3  '3 positional arguments'
              370  STORE_FAST               'Z_axis_pid'

 L.1131       372  LOAD_GLOBAL              cv2
              374  LOAD_METHOD              CascadeClassifier
              376  LOAD_STR                 '/home/pi/yahboom-raspblock/haarcascade_profileface.xml'
              378  CALL_METHOD_1         1  '1 positional argument'
              380  STORE_FAST               'face_haar'

 L.1134       382  LOAD_GLOBAL              tf
              384  LOAD_ATTR                compat
              386  LOAD_ATTR                v1
              388  LOAD_ATTR                Session
              390  LOAD_GLOBAL              detection_graph
              392  LOAD_CONST               ('graph',)
              394  CALL_FUNCTION_KW_1     1  '1 total positional and keyword args'
              396  STORE_FAST               'sess'

 L.1136       398  LOAD_GLOBAL              camservoInitFunction
              400  CALL_FUNCTION_0       0  '0 positional arguments'
              402  POP_TOP          

 L.1139       404  LOAD_FAST                'g_camera'
              406  LOAD_METHOD              read
              408  CALL_METHOD_0         0  '0 positional arguments'
              410  UNPACK_SEQUENCE_2     2 
              412  STORE_FAST               'retval'
              414  STORE_FAST               'frame'

 L.1141       416  LOAD_GLOBAL              meanshift_X
              418  LOAD_GLOBAL              meanshift_Y
              420  LOAD_GLOBAL              meanshift_width
              422  LOAD_GLOBAL              meanshift_high
              424  BUILD_TUPLE_4         4 
              426  STORE_FAST               'track_window'

 L.1143       428  LOAD_FAST                'frame'
              430  LOAD_GLOBAL              meanshift_Y
              432  LOAD_GLOBAL              meanshift_Y
              434  LOAD_GLOBAL              meanshift_high
              436  BINARY_ADD       
              438  BUILD_SLICE_2         2 
              440  LOAD_GLOBAL              meanshift_X
              442  LOAD_GLOBAL              meanshift_X
              444  LOAD_GLOBAL              meanshift_width
              446  BINARY_ADD       
              448  BUILD_SLICE_2         2 
              450  BUILD_TUPLE_2         2 
              452  BINARY_SUBSCR    
              454  STORE_FAST               'roi'

 L.1146       456  LOAD_GLOBAL              cv2
              458  LOAD_METHOD              cvtColor
              460  LOAD_FAST                'frame'
              462  LOAD_GLOBAL              cv2
              464  LOAD_ATTR                COLOR_BGR2HSV
              466  CALL_METHOD_2         2  '2 positional arguments'
              468  STORE_FAST               'hsv_roi'

 L.1148       470  LOAD_GLOBAL              cv2
              472  LOAD_METHOD              inRange
              474  LOAD_FAST                'hsv_roi'
              476  LOAD_GLOBAL              np
              478  LOAD_METHOD              array
              480  LOAD_CONST               (0.0, 60.0, 32.0)
              482  CALL_METHOD_1         1  '1 positional argument'
              484  LOAD_GLOBAL              np
              486  LOAD_METHOD              array
              488  LOAD_CONST               (180.0, 255.0, 255.0)
              490  CALL_METHOD_1         1  '1 positional argument'
              492  CALL_METHOD_3         3  '3 positional arguments'
              494  STORE_FAST               'mask'

 L.1150       496  LOAD_GLOBAL              cv2
              498  LOAD_METHOD              calcHist
              500  LOAD_FAST                'hsv_roi'
              502  BUILD_LIST_1          1 
              504  LOAD_CONST               0
              506  BUILD_LIST_1          1 
              508  LOAD_FAST                'mask'
              510  LOAD_CONST               180
              512  BUILD_LIST_1          1 
              514  LOAD_CONST               0
              516  LOAD_CONST               180
              518  BUILD_LIST_2          2 
              520  CALL_METHOD_5         5  '5 positional arguments'
              522  STORE_FAST               'roi_hist'

 L.1152       524  LOAD_GLOBAL              cv2
              526  LOAD_METHOD              normalize
              528  LOAD_FAST                'roi_hist'
              530  LOAD_FAST                'roi_hist'
              532  LOAD_CONST               0
              534  LOAD_CONST               255
              536  LOAD_GLOBAL              cv2
              538  LOAD_ATTR                NORM_MINMAX
              540  CALL_METHOD_5         5  '5 positional arguments'
              542  POP_TOP          

 L.1154       544  LOAD_GLOBAL              cv2
              546  LOAD_ATTR                TERM_CRITERIA_EPS
              548  LOAD_GLOBAL              cv2
              550  LOAD_ATTR                TERM_CRITERIA_COUNT
              552  BINARY_OR        
              554  LOAD_CONST               10
              556  LOAD_CONST               1
              558  BUILD_TUPLE_3         3 
              560  STORE_FAST               'term_crit'

 L.1155       562  LOAD_GLOBAL              robot
              564  LOAD_METHOD              BoardData_Get
              566  LOAD_CONST               0
              568  CALL_METHOD_1         1  '1 positional argument'
              570  POP_TOP          

 L.1157   572_574  SETUP_LOOP         3828  'to 3828'

 L.1158       576  LOAD_GLOBAL              g_mode
              578  LOAD_STR                 'auto_drive'
              580  COMPARE_OP               ==
          582_584  POP_JUMP_IF_FALSE   762  'to 762'

 L.1159       586  LOAD_FAST                'g_camera'
              588  LOAD_METHOD              get
              590  LOAD_GLOBAL              cv2
              592  LOAD_ATTR                CAP_PROP_FRAME_WIDTH
              594  CALL_METHOD_1         1  '1 positional argument'
              596  LOAD_CONST               1920
              598  COMPARE_OP               !=
          600_602  POP_JUMP_IF_FALSE   936  'to 936'

 L.1160       604  LOAD_GLOBAL              print
              606  LOAD_STR                 '################# 0 1920*1080'
              608  CALL_FUNCTION_1       1  '1 positional argument'
              610  POP_TOP          

 L.1161       612  LOAD_FAST                'g_camera'
              614  LOAD_METHOD              release
              616  CALL_METHOD_0         0  '0 positional arguments'
              618  POP_TOP          

 L.1162       620  LOAD_GLOBAL              print
              622  LOAD_STR                 '################# 1 1920*1080'
              624  CALL_FUNCTION_1       1  '1 positional argument'
              626  POP_TOP          

 L.1163       628  LOAD_GLOBAL              cv2
              630  LOAD_METHOD              VideoCapture
              632  LOAD_CONST               0
              634  CALL_METHOD_1         1  '1 positional argument'
              636  STORE_FAST               'g_camera'

 L.1164       638  LOAD_GLOBAL              print
              640  LOAD_STR                 '################# 2 1920*1080'
              642  CALL_FUNCTION_1       1  '1 positional argument'
              644  POP_TOP          

 L.1165       646  LOAD_FAST                'g_camera'
              648  LOAD_METHOD              set
              650  LOAD_CONST               3
              652  LOAD_CONST               1920
              654  CALL_METHOD_2         2  '2 positional arguments'
              656  POP_TOP          

 L.1166       658  LOAD_FAST                'g_camera'
              660  LOAD_METHOD              set
              662  LOAD_CONST               4
              664  LOAD_CONST               1080
              666  CALL_METHOD_2         2  '2 positional arguments'
              668  POP_TOP          

 L.1167       670  LOAD_FAST                'g_camera'
              672  LOAD_METHOD              set
              674  LOAD_CONST               5
              676  LOAD_CONST               30
              678  CALL_METHOD_2         2  '2 positional arguments'
              680  POP_TOP          

 L.1168       682  LOAD_FAST                'g_camera'
              684  LOAD_METHOD              set
              686  LOAD_GLOBAL              cv2
              688  LOAD_ATTR                CAP_PROP_FOURCC
              690  LOAD_GLOBAL              cv2
              692  LOAD_ATTR                VideoWriter
              694  LOAD_METHOD              fourcc
              696  LOAD_STR                 'M'
              698  LOAD_STR                 'J'
              700  LOAD_STR                 'P'
              702  LOAD_STR                 'G'
              704  CALL_METHOD_4         4  '4 positional arguments'
              706  CALL_METHOD_2         2  '2 positional arguments'
              708  POP_TOP          

 L.1169       710  LOAD_FAST                'g_camera'
              712  LOAD_METHOD              set
              714  LOAD_GLOBAL              cv2
              716  LOAD_ATTR                CAP_PROP_BRIGHTNESS
              718  LOAD_CONST               40
              720  CALL_METHOD_2         2  '2 positional arguments'
              722  POP_TOP          

 L.1170       724  LOAD_FAST                'g_camera'
              726  LOAD_METHOD              set
              728  LOAD_GLOBAL              cv2
              730  LOAD_ATTR                CAP_PROP_CONTRAST
              732  LOAD_CONST               50
              734  CALL_METHOD_2         2  '2 positional arguments'
              736  POP_TOP          

 L.1171       738  LOAD_FAST                'g_camera'
              740  LOAD_METHOD              set
              742  LOAD_GLOBAL              cv2
              744  LOAD_ATTR                CAP_PROP_EXPOSURE
              746  LOAD_CONST               156
              748  CALL_METHOD_2         2  '2 positional arguments'
              750  POP_TOP          

 L.1172       752  LOAD_GLOBAL              print
              754  LOAD_STR                 '################# 3 1920*1080'
              756  CALL_FUNCTION_1       1  '1 positional argument'
              758  POP_TOP          
              760  JUMP_FORWARD        936  'to 936'
            762_0  COME_FROM           582  '582'

 L.1174       762  LOAD_FAST                'g_camera'
              764  LOAD_METHOD              get
              766  LOAD_GLOBAL              cv2
              768  LOAD_ATTR                CAP_PROP_FRAME_WIDTH
              770  CALL_METHOD_1         1  '1 positional argument'
              772  LOAD_CONST               320
              774  COMPARE_OP               !=
          776_778  POP_JUMP_IF_FALSE   936  'to 936'

 L.1175       780  LOAD_GLOBAL              print
              782  LOAD_STR                 '################# 0 320*240'
              784  CALL_FUNCTION_1       1  '1 positional argument'
              786  POP_TOP          

 L.1176       788  LOAD_FAST                'g_camera'
              790  LOAD_METHOD              release
              792  CALL_METHOD_0         0  '0 positional arguments'
              794  POP_TOP          

 L.1177       796  LOAD_GLOBAL              print
              798  LOAD_STR                 '################# 1 320*240'
              800  CALL_FUNCTION_1       1  '1 positional argument'
              802  POP_TOP          

 L.1178       804  LOAD_GLOBAL              cv2
              806  LOAD_METHOD              VideoCapture
              808  LOAD_CONST               0
              810  CALL_METHOD_1         1  '1 positional argument'
              812  STORE_FAST               'g_camera'

 L.1179       814  LOAD_GLOBAL              print
              816  LOAD_STR                 '################# 2 320*240'
              818  CALL_FUNCTION_1       1  '1 positional argument'
              820  POP_TOP          

 L.1180       822  LOAD_FAST                'g_camera'
              824  LOAD_METHOD              set
              826  LOAD_CONST               3
              828  LOAD_CONST               320
              830  CALL_METHOD_2         2  '2 positional arguments'
              832  POP_TOP          

 L.1181       834  LOAD_FAST                'g_camera'
              836  LOAD_METHOD              set
              838  LOAD_CONST               4
              840  LOAD_CONST               240
              842  CALL_METHOD_2         2  '2 positional arguments'
              844  POP_TOP          

 L.1182       846  LOAD_FAST                'g_camera'
              848  LOAD_METHOD              set
              850  LOAD_CONST               5
              852  LOAD_CONST               120
              854  CALL_METHOD_2         2  '2 positional arguments'
              856  POP_TOP          

 L.1183       858  LOAD_FAST                'g_camera'
              860  LOAD_METHOD              set
              862  LOAD_GLOBAL              cv2
              864  LOAD_ATTR                CAP_PROP_FOURCC
              866  LOAD_GLOBAL              cv2
              868  LOAD_ATTR                VideoWriter
              870  LOAD_METHOD              fourcc
              872  LOAD_STR                 'M'
              874  LOAD_STR                 'J'
              876  LOAD_STR                 'P'
              878  LOAD_STR                 'G'
              880  CALL_METHOD_4         4  '4 positional arguments'
              882  CALL_METHOD_2         2  '2 positional arguments'
              884  POP_TOP          

 L.1184       886  LOAD_FAST                'g_camera'
              888  LOAD_METHOD              set
              890  LOAD_GLOBAL              cv2
              892  LOAD_ATTR                CAP_PROP_BRIGHTNESS
              894  LOAD_CONST               40
              896  CALL_METHOD_2         2  '2 positional arguments'
              898  POP_TOP          

 L.1185       900  LOAD_FAST                'g_camera'
              902  LOAD_METHOD              set
              904  LOAD_GLOBAL              cv2
              906  LOAD_ATTR                CAP_PROP_CONTRAST
              908  LOAD_CONST               50
              910  CALL_METHOD_2         2  '2 positional arguments'
              912  POP_TOP          

 L.1186       914  LOAD_FAST                'g_camera'
              916  LOAD_METHOD              set
              918  LOAD_GLOBAL              cv2
              920  LOAD_ATTR                CAP_PROP_EXPOSURE
              922  LOAD_CONST               156
              924  CALL_METHOD_2         2  '2 positional arguments'
              926  POP_TOP          

 L.1187       928  LOAD_GLOBAL              print
              930  LOAD_STR                 '################# 3 320*240'
              932  CALL_FUNCTION_1       1  '1 positional argument'
              934  POP_TOP          
            936_0  COME_FROM           776  '776'
            936_1  COME_FROM           760  '760'
            936_2  COME_FROM           600  '600'

 L.1189       936  LOAD_FAST                'g_camera'
              938  LOAD_METHOD              read
              940  CALL_METHOD_0         0  '0 positional arguments'
              942  UNPACK_SEQUENCE_2     2 
              944  STORE_FAST               'retval'
              946  STORE_FAST               'frame'

 L.1190       948  LOAD_FAST                'retval'
              950  LOAD_CONST               False
              952  COMPARE_OP               ==
          954_956  POP_JUMP_IF_FALSE   970  'to 970'

 L.1191       958  LOAD_GLOBAL              print
              960  LOAD_STR                 'read camera err!'
              962  CALL_FUNCTION_1       1  '1 positional argument'
              964  POP_TOP          

 L.1192   966_968  CONTINUE            576  'to 576'
            970_0  COME_FROM           954  '954'

 L.1195       970  LOAD_FAST                'fps'
              972  LOAD_CONST               1
              974  BINARY_ADD       
              976  STORE_FAST               'fps'

 L.1196       978  LOAD_FAST                'fps'
              980  LOAD_GLOBAL              time
              982  LOAD_METHOD              time
              984  CALL_METHOD_0         0  '0 positional arguments'
              986  LOAD_FAST                't_start'
              988  BINARY_SUBTRACT  
              990  BINARY_TRUE_DIVIDE
              992  STORE_FAST               'mfps'

 L.1199       994  LOAD_GLOBAL              g_mode
              996  LOAD_STR                 'target_track'
              998  COMPARE_OP               ==
         1000_1002  POP_JUMP_IF_FALSE  1840  'to 1840'

 L.1200      1004  LOAD_GLOBAL              g_target_mode
             1006  LOAD_STR                 'face_track'
             1008  COMPARE_OP               ==
         1010_1012  POP_JUMP_IF_FALSE  1222  'to 1222'

 L.1202      1014  LOAD_GLOBAL              cv2
             1016  LOAD_METHOD              cvtColor
             1018  LOAD_FAST                'frame'
             1020  LOAD_GLOBAL              cv2
             1022  LOAD_ATTR                COLOR_BGR2GRAY
             1024  CALL_METHOD_2         2  '2 positional arguments'
             1026  STORE_FAST               'gray_img'

 L.1203      1028  LOAD_FAST                'face_haar'
             1030  LOAD_METHOD              detectMultiScale
             1032  LOAD_FAST                'gray_img'
             1034  LOAD_CONST               1.1
             1036  LOAD_CONST               3
             1038  CALL_METHOD_3         3  '3 positional arguments'
             1040  STORE_FAST               'faces'

 L.1204      1042  LOAD_GLOBAL              len
             1044  LOAD_FAST                'faces'
             1046  CALL_FUNCTION_1       1  '1 positional argument'
             1048  LOAD_CONST               0
             1050  COMPARE_OP               >
         1052_1054  POP_JUMP_IF_FALSE  1836  'to 1836'

 L.1205      1056  LOAD_FAST                'faces'
             1058  LOAD_CONST               0
             1060  BINARY_SUBSCR    
             1062  UNPACK_SEQUENCE_4     4 
             1064  STORE_GLOBAL             face_x
             1066  STORE_GLOBAL             face_y
             1068  STORE_GLOBAL             face_w
             1070  STORE_GLOBAL             face_h

 L.1207      1072  LOAD_GLOBAL              cv2
             1074  LOAD_METHOD              rectangle
             1076  LOAD_FAST                'frame'
             1078  LOAD_GLOBAL              face_x
             1080  LOAD_GLOBAL              face_y
             1082  BUILD_TUPLE_2         2 
             1084  LOAD_GLOBAL              face_x
             1086  LOAD_GLOBAL              face_w
             1088  BINARY_ADD       
             1090  LOAD_GLOBAL              face_y
             1092  LOAD_GLOBAL              face_h
             1094  BINARY_ADD       
             1096  BUILD_TUPLE_2         2 
             1098  LOAD_CONST               (0, 255, 0)
             1100  LOAD_CONST               2
             1102  CALL_METHOD_5         5  '5 positional arguments'
             1104  POP_TOP          

 L.1211      1106  LOAD_GLOBAL              face_x
             1108  LOAD_GLOBAL              face_w
             1110  LOAD_CONST               2
             1112  BINARY_TRUE_DIVIDE
             1114  BINARY_ADD       
             1116  LOAD_FAST                'xservo_pid'
             1118  STORE_ATTR               SystemOutput

 L.1212      1120  LOAD_FAST                'xservo_pid'
             1122  LOAD_METHOD              SetStepSignal
             1124  LOAD_CONST               150
             1126  CALL_METHOD_1         1  '1 positional argument'
             1128  POP_TOP          

 L.1213      1130  LOAD_FAST                'xservo_pid'
             1132  LOAD_METHOD              SetInertiaTime
             1134  LOAD_CONST               0.01
             1136  LOAD_CONST               0.1
             1138  CALL_METHOD_2         2  '2 positional arguments'
             1140  POP_TOP          

 L.1214      1142  LOAD_GLOBAL              int
             1144  LOAD_CONST               1500
             1146  LOAD_FAST                'xservo_pid'
             1148  LOAD_ATTR                SystemOutput
             1150  BINARY_ADD       
             1152  CALL_FUNCTION_1       1  '1 positional argument'
             1154  STORE_GLOBAL             target_valuex

 L.1216      1156  LOAD_GLOBAL              face_y
             1158  LOAD_GLOBAL              face_h
             1160  LOAD_CONST               2
             1162  BINARY_TRUE_DIVIDE
             1164  BINARY_ADD       
             1166  LOAD_FAST                'yservo_pid'
             1168  STORE_ATTR               SystemOutput

 L.1217      1170  LOAD_FAST                'yservo_pid'
             1172  LOAD_METHOD              SetStepSignal
             1174  LOAD_CONST               120
             1176  CALL_METHOD_1         1  '1 positional argument'
             1178  POP_TOP          

 L.1218      1180  LOAD_FAST                'yservo_pid'
             1182  LOAD_METHOD              SetInertiaTime
             1184  LOAD_CONST               0.01
             1186  LOAD_CONST               0.1
             1188  CALL_METHOD_2         2  '2 positional arguments'
             1190  POP_TOP          

 L.1219      1192  LOAD_GLOBAL              int
             1194  LOAD_CONST               1500
             1196  LOAD_FAST                'yservo_pid'
             1198  LOAD_ATTR                SystemOutput
             1200  BINARY_SUBTRACT  
             1202  CALL_FUNCTION_1       1  '1 positional argument'
             1204  STORE_GLOBAL             target_valuey

 L.1221      1206  LOAD_GLOBAL              robot
             1208  LOAD_METHOD              Servo_control
             1210  LOAD_GLOBAL              target_valuex
             1212  LOAD_GLOBAL              target_valuey
             1214  CALL_METHOD_2         2  '2 positional arguments'
             1216  POP_TOP          
         1218_1220  JUMP_ABSOLUTE      3728  'to 3728'
           1222_0  COME_FROM          1010  '1010'

 L.1222      1222  LOAD_GLOBAL              g_target_mode
             1224  LOAD_STR                 'color_track'
             1226  COMPARE_OP               ==
         1228_1230  POP_JUMP_IF_FALSE  1536  'to 1536'

 L.1223      1232  LOAD_GLOBAL              cv2
             1234  LOAD_METHOD              GaussianBlur
             1236  LOAD_FAST                'frame'
             1238  LOAD_CONST               (5, 5)
             1240  LOAD_CONST               0
             1242  CALL_METHOD_3         3  '3 positional arguments'
             1244  STORE_FAST               'frame_'

 L.1224      1246  LOAD_GLOBAL              cv2
             1248  LOAD_METHOD              cvtColor
             1250  LOAD_FAST                'frame'
             1252  LOAD_GLOBAL              cv2
             1254  LOAD_ATTR                COLOR_BGR2HSV
             1256  CALL_METHOD_2         2  '2 positional arguments'
             1258  STORE_FAST               'hsv'

 L.1225      1260  LOAD_GLOBAL              cv2
             1262  LOAD_METHOD              inRange
             1264  LOAD_FAST                'hsv'
             1266  LOAD_GLOBAL              color_lower
             1268  LOAD_GLOBAL              color_upper
             1270  CALL_METHOD_3         3  '3 positional arguments'
             1272  STORE_FAST               'mask'

 L.1226      1274  LOAD_GLOBAL              cv2
             1276  LOAD_ATTR                erode
             1278  LOAD_FAST                'mask'
             1280  LOAD_CONST               None
             1282  LOAD_CONST               2
             1284  LOAD_CONST               ('iterations',)
             1286  CALL_FUNCTION_KW_3     3  '3 total positional and keyword args'
             1288  STORE_FAST               'mask'

 L.1227      1290  LOAD_GLOBAL              cv2
             1292  LOAD_ATTR                dilate
             1294  LOAD_FAST                'mask'
             1296  LOAD_CONST               None
             1298  LOAD_CONST               2
             1300  LOAD_CONST               ('iterations',)
             1302  CALL_FUNCTION_KW_3     3  '3 total positional and keyword args'
             1304  STORE_FAST               'mask'

 L.1228      1306  LOAD_GLOBAL              cv2
             1308  LOAD_METHOD              GaussianBlur
             1310  LOAD_FAST                'mask'
             1312  LOAD_CONST               (3, 3)
             1314  LOAD_CONST               0
             1316  CALL_METHOD_3         3  '3 positional arguments'
             1318  STORE_FAST               'mask'

 L.1229      1320  LOAD_GLOBAL              cv2
             1322  LOAD_METHOD              findContours
             1324  LOAD_FAST                'mask'
             1326  LOAD_METHOD              copy
             1328  CALL_METHOD_0         0  '0 positional arguments'
             1330  LOAD_GLOBAL              cv2
             1332  LOAD_ATTR                RETR_EXTERNAL
             1334  LOAD_GLOBAL              cv2
             1336  LOAD_ATTR                CHAIN_APPROX_SIMPLE
             1338  CALL_METHOD_3         3  '3 positional arguments'
             1340  LOAD_CONST               -2
             1342  BINARY_SUBSCR    
             1344  STORE_FAST               'cnts'

 L.1230      1346  LOAD_GLOBAL              len
             1348  LOAD_FAST                'cnts'
             1350  CALL_FUNCTION_1       1  '1 positional argument'
             1352  LOAD_CONST               0
             1354  COMPARE_OP               >
         1356_1358  POP_JUMP_IF_FALSE  1836  'to 1836'

 L.1231      1360  LOAD_GLOBAL              max
             1362  LOAD_FAST                'cnts'
             1364  LOAD_GLOBAL              cv2
             1366  LOAD_ATTR                contourArea
             1368  LOAD_CONST               ('key',)
             1370  CALL_FUNCTION_KW_2     2  '2 total positional and keyword args'
             1372  STORE_FAST               'cnt'

 L.1232      1374  LOAD_GLOBAL              cv2
             1376  LOAD_METHOD              minEnclosingCircle
             1378  LOAD_FAST                'cnt'
             1380  CALL_METHOD_1         1  '1 positional argument'
             1382  UNPACK_SEQUENCE_2     2 
             1384  UNPACK_SEQUENCE_2     2 
             1386  STORE_FAST               'color_x'
             1388  STORE_FAST               'color_y'
             1390  STORE_FAST               'color_radius'

 L.1233      1392  LOAD_FAST                'color_radius'
             1394  LOAD_CONST               10
             1396  COMPARE_OP               >
         1398_1400  POP_JUMP_IF_FALSE  1836  'to 1836'

 L.1235      1402  LOAD_GLOBAL              cv2
             1404  LOAD_METHOD              circle
             1406  LOAD_FAST                'frame'
             1408  LOAD_GLOBAL              int
             1410  LOAD_FAST                'color_x'
             1412  CALL_FUNCTION_1       1  '1 positional argument'
             1414  LOAD_GLOBAL              int
             1416  LOAD_FAST                'color_y'
             1418  CALL_FUNCTION_1       1  '1 positional argument'
             1420  BUILD_TUPLE_2         2 
             1422  LOAD_GLOBAL              int
             1424  LOAD_FAST                'color_radius'
             1426  CALL_FUNCTION_1       1  '1 positional argument'
             1428  LOAD_CONST               (255, 0, 255)
             1430  LOAD_CONST               2
             1432  CALL_METHOD_5         5  '5 positional arguments'
             1434  POP_TOP          

 L.1237      1436  LOAD_FAST                'color_x'
             1438  LOAD_FAST                'xservo_pid'
             1440  STORE_ATTR               SystemOutput

 L.1238      1442  LOAD_FAST                'xservo_pid'
             1444  LOAD_METHOD              SetStepSignal
             1446  LOAD_CONST               150
             1448  CALL_METHOD_1         1  '1 positional argument'
             1450  POP_TOP          

 L.1239      1452  LOAD_FAST                'xservo_pid'
             1454  LOAD_METHOD              SetInertiaTime
             1456  LOAD_CONST               0.01
             1458  LOAD_CONST               0.1
             1460  CALL_METHOD_2         2  '2 positional arguments'
             1462  POP_TOP          

 L.1240      1464  LOAD_GLOBAL              int
             1466  LOAD_CONST               1500
             1468  LOAD_FAST                'xservo_pid'
             1470  LOAD_ATTR                SystemOutput
             1472  BINARY_ADD       
             1474  CALL_FUNCTION_1       1  '1 positional argument'
             1476  STORE_GLOBAL             target_valuex

 L.1242      1478  LOAD_FAST                'color_y'
             1480  LOAD_FAST                'yservo_pid'
             1482  STORE_ATTR               SystemOutput

 L.1243      1484  LOAD_FAST                'yservo_pid'
             1486  LOAD_METHOD              SetStepSignal
             1488  LOAD_CONST               150
             1490  CALL_METHOD_1         1  '1 positional argument'
             1492  POP_TOP          

 L.1244      1494  LOAD_FAST                'yservo_pid'
             1496  LOAD_METHOD              SetInertiaTime
             1498  LOAD_CONST               0.01
             1500  LOAD_CONST               0.1
             1502  CALL_METHOD_2         2  '2 positional arguments'
             1504  POP_TOP          

 L.1245      1506  LOAD_GLOBAL              int
             1508  LOAD_CONST               1500
             1510  LOAD_FAST                'yservo_pid'
             1512  LOAD_ATTR                SystemOutput
             1514  BINARY_SUBTRACT  
             1516  CALL_FUNCTION_1       1  '1 positional argument'
             1518  STORE_GLOBAL             target_valuey

 L.1247      1520  LOAD_GLOBAL              robot
             1522  LOAD_METHOD              Servo_control
             1524  LOAD_GLOBAL              target_valuex
             1526  LOAD_GLOBAL              target_valuey
             1528  CALL_METHOD_2         2  '2 positional arguments'
             1530  POP_TOP          
         1532_1534  JUMP_ABSOLUTE      3728  'to 3728'
           1536_0  COME_FROM          1228  '1228'

 L.1248      1536  LOAD_GLOBAL              g_target_mode
             1538  LOAD_STR                 'meanshift_track'
             1540  COMPARE_OP               ==
         1542_1544  POP_JUMP_IF_FALSE  3728  'to 3728'

 L.1249      1546  LOAD_GLOBAL              meanshift_update_flag
             1548  LOAD_CONST               1
             1550  COMPARE_OP               ==
         1552_1554  POP_JUMP_IF_FALSE  1732  'to 1732'

 L.1250      1556  LOAD_GLOBAL              print
             1558  LOAD_STR                 'Meanshift init!'
             1560  CALL_FUNCTION_1       1  '1 positional argument'
             1562  POP_TOP          

 L.1252      1564  LOAD_GLOBAL              meanshift_X
             1566  LOAD_GLOBAL              meanshift_Y
             1568  LOAD_GLOBAL              meanshift_width
             1570  LOAD_GLOBAL              meanshift_high
             1572  BUILD_TUPLE_4         4 
             1574  STORE_FAST               'track_window'

 L.1254      1576  LOAD_FAST                'frame'
             1578  LOAD_GLOBAL              meanshift_Y
             1580  LOAD_GLOBAL              meanshift_Y
             1582  LOAD_GLOBAL              meanshift_high
             1584  BINARY_ADD       
             1586  BUILD_SLICE_2         2 
             1588  LOAD_GLOBAL              meanshift_X
             1590  LOAD_GLOBAL              meanshift_X
             1592  LOAD_GLOBAL              meanshift_width
             1594  BINARY_ADD       
             1596  BUILD_SLICE_2         2 
             1598  BUILD_TUPLE_2         2 
             1600  BINARY_SUBSCR    
             1602  STORE_FAST               'roi'

 L.1255      1604  LOAD_GLOBAL              cv2
             1606  LOAD_METHOD              rectangle
             1608  LOAD_FAST                'frame'
             1610  LOAD_CONST               (140, 100)
             1612  LOAD_CONST               (180, 140)
             1614  LOAD_CONST               255
             1616  LOAD_CONST               2
             1618  CALL_METHOD_5         5  '5 positional arguments'
             1620  STORE_FAST               'frame'

 L.1257      1622  LOAD_GLOBAL              cv2
             1624  LOAD_METHOD              cvtColor
             1626  LOAD_FAST                'frame'
             1628  LOAD_GLOBAL              cv2
             1630  LOAD_ATTR                COLOR_BGR2HSV
             1632  CALL_METHOD_2         2  '2 positional arguments'
             1634  STORE_FAST               'hsv_roi'

 L.1259      1636  LOAD_GLOBAL              cv2
             1638  LOAD_METHOD              inRange
             1640  LOAD_FAST                'hsv_roi'
             1642  LOAD_GLOBAL              np
             1644  LOAD_METHOD              array
             1646  LOAD_CONST               (0.0, 60.0, 32.0)
             1648  CALL_METHOD_1         1  '1 positional argument'
             1650  LOAD_GLOBAL              np
             1652  LOAD_METHOD              array
             1654  LOAD_CONST               (180.0, 255.0, 255.0)
             1656  CALL_METHOD_1         1  '1 positional argument'
             1658  CALL_METHOD_3         3  '3 positional arguments'
             1660  STORE_FAST               'mask'

 L.1261      1662  LOAD_GLOBAL              cv2
             1664  LOAD_METHOD              calcHist
             1666  LOAD_FAST                'hsv_roi'
             1668  BUILD_LIST_1          1 
             1670  LOAD_CONST               0
             1672  BUILD_LIST_1          1 
             1674  LOAD_FAST                'mask'
             1676  LOAD_CONST               180
             1678  BUILD_LIST_1          1 
             1680  LOAD_CONST               0
             1682  LOAD_CONST               180
             1684  BUILD_LIST_2          2 
             1686  CALL_METHOD_5         5  '5 positional arguments'
             1688  STORE_FAST               'roi_hist'

 L.1263      1690  LOAD_GLOBAL              cv2
             1692  LOAD_METHOD              normalize
             1694  LOAD_FAST                'roi_hist'
             1696  LOAD_FAST                'roi_hist'
             1698  LOAD_CONST               0
             1700  LOAD_CONST               255
             1702  LOAD_GLOBAL              cv2
             1704  LOAD_ATTR                NORM_MINMAX
             1706  CALL_METHOD_5         5  '5 positional arguments'
             1708  POP_TOP          

 L.1265      1710  LOAD_GLOBAL              cv2
             1712  LOAD_ATTR                TERM_CRITERIA_EPS
             1714  LOAD_GLOBAL              cv2
             1716  LOAD_ATTR                TERM_CRITERIA_COUNT
             1718  BINARY_OR        
             1720  LOAD_CONST               10
             1722  LOAD_CONST               1
             1724  BUILD_TUPLE_3         3 
             1726  STORE_FAST               'term_crit'

 L.1266      1728  LOAD_CONST               0
             1730  STORE_GLOBAL             meanshift_update_flag
           1732_0  COME_FROM          1552  '1552'

 L.1267      1732  LOAD_GLOBAL              cv2
             1734  LOAD_METHOD              cvtColor
             1736  LOAD_FAST                'frame'
             1738  LOAD_GLOBAL              cv2
             1740  LOAD_ATTR                COLOR_BGR2HSV
             1742  CALL_METHOD_2         2  '2 positional arguments'
             1744  STORE_FAST               'hsv'

 L.1268      1746  LOAD_GLOBAL              cv2
             1748  LOAD_METHOD              calcBackProject
             1750  LOAD_FAST                'hsv'
             1752  BUILD_LIST_1          1 
             1754  LOAD_CONST               0
             1756  BUILD_LIST_1          1 
             1758  LOAD_FAST                'roi_hist'
             1760  LOAD_CONST               0
             1762  LOAD_CONST               180
             1764  BUILD_LIST_2          2 
             1766  LOAD_CONST               1
             1768  CALL_METHOD_5         5  '5 positional arguments'
             1770  STORE_FAST               'dst'

 L.1270      1772  LOAD_GLOBAL              cv2
             1774  LOAD_METHOD              meanShift
             1776  LOAD_FAST                'dst'
             1778  LOAD_FAST                'track_window'
             1780  LOAD_FAST                'term_crit'
             1782  CALL_METHOD_3         3  '3 positional arguments'
             1784  UNPACK_SEQUENCE_2     2 
             1786  STORE_FAST               'ret'
             1788  STORE_FAST               'track_window'

 L.1272      1790  LOAD_FAST                'track_window'
             1792  UNPACK_SEQUENCE_4     4 
             1794  STORE_FAST               'x'
             1796  STORE_FAST               'y'
             1798  STORE_FAST               'w'
             1800  STORE_FAST               'h'

 L.1273      1802  LOAD_GLOBAL              cv2
             1804  LOAD_METHOD              rectangle
             1806  LOAD_FAST                'frame'
             1808  LOAD_FAST                'x'
             1810  LOAD_FAST                'y'
             1812  BUILD_TUPLE_2         2 
             1814  LOAD_FAST                'x'
             1816  LOAD_FAST                'w'
             1818  BINARY_ADD       
             1820  LOAD_FAST                'y'
             1822  LOAD_FAST                'h'
             1824  BINARY_ADD       
             1826  BUILD_TUPLE_2         2 
             1828  LOAD_CONST               255
             1830  LOAD_CONST               2
             1832  CALL_METHOD_5         5  '5 positional arguments'
             1834  POP_TOP          
           1836_0  COME_FROM          1398  '1398'
           1836_1  COME_FROM          1356  '1356'
           1836_2  COME_FROM          1052  '1052'
         1836_1838  JUMP_FORWARD       3728  'to 3728'
           1840_0  COME_FROM          1000  '1000'

 L.1274      1840  LOAD_GLOBAL              g_mode
             1842  LOAD_STR                 'tag_identification'
             1844  COMPARE_OP               ==
         1846_1848  POP_JUMP_IF_FALSE  2812  'to 2812'

 L.1275      1850  LOAD_GLOBAL              g_tag_identify_switch
             1852  LOAD_STR                 'open'
             1854  COMPARE_OP               ==
         1856_1858  POP_JUMP_IF_FALSE  3728  'to 3728'

 L.1276      1860  LOAD_GLOBAL              g_tag_select
             1862  LOAD_STR                 'qrcode'
             1864  COMPARE_OP               ==
         1866_1868  POP_JUMP_IF_FALSE  2046  'to 2046'

 L.1277      1870  LOAD_GLOBAL              cv2
             1872  LOAD_METHOD              cvtColor
             1874  LOAD_FAST                'frame'
             1876  LOAD_GLOBAL              cv2
             1878  LOAD_ATTR                COLOR_BGR2GRAY
             1880  CALL_METHOD_2         2  '2 positional arguments'
             1882  STORE_FAST               'gray_img'

 L.1278      1884  LOAD_GLOBAL              pyzbar
             1886  LOAD_METHOD              decode
             1888  LOAD_FAST                'gray_img'
             1890  CALL_METHOD_1         1  '1 positional argument'
             1892  STORE_FAST               'barcodes'

 L.1279      1894  SETUP_LOOP         2042  'to 2042'
             1896  LOAD_FAST                'barcodes'
             1898  GET_ITER         
           1900_0  COME_FROM          2024  '2024'
             1900  FOR_ITER           2040  'to 2040'
             1902  STORE_FAST               'barcode'

 L.1282      1904  LOAD_FAST                'barcode'
             1906  LOAD_ATTR                rect
             1908  UNPACK_SEQUENCE_4     4 
             1910  STORE_FAST               'x'
             1912  STORE_FAST               'y'
             1914  STORE_FAST               'w'
             1916  STORE_FAST               'h'

 L.1283      1918  LOAD_GLOBAL              cv2
             1920  LOAD_METHOD              rectangle
             1922  LOAD_FAST                'frame'
             1924  LOAD_FAST                'x'
             1926  LOAD_FAST                'y'
             1928  BUILD_TUPLE_2         2 
             1930  LOAD_FAST                'x'
             1932  LOAD_FAST                'w'
             1934  BINARY_ADD       
             1936  LOAD_FAST                'y'
             1938  LOAD_FAST                'h'
             1940  BINARY_ADD       
             1942  BUILD_TUPLE_2         2 
             1944  LOAD_CONST               (0, 225, 0)
             1946  LOAD_CONST               2
             1948  CALL_METHOD_5         5  '5 positional arguments'
             1950  POP_TOP          

 L.1286      1952  LOAD_FAST                'barcode'
             1954  LOAD_ATTR                data
             1956  LOAD_METHOD              decode
             1958  LOAD_STR                 'utf-8'
             1960  CALL_METHOD_1         1  '1 positional argument'
             1962  STORE_FAST               'barcodeData'

 L.1287      1964  LOAD_FAST                'barcode'
             1966  LOAD_ATTR                type
             1968  STORE_FAST               'barcodeType'

 L.1289      1970  LOAD_STR                 '{} ({})'
             1972  LOAD_METHOD              format
             1974  LOAD_FAST                'barcodeData'
             1976  LOAD_FAST                'barcodeType'
             1978  CALL_METHOD_2         2  '2 positional arguments'
             1980  STORE_FAST               'text'

 L.1290      1982  LOAD_GLOBAL              cv2
             1984  LOAD_METHOD              putText
             1986  LOAD_FAST                'frame'
             1988  LOAD_FAST                'text'
             1990  LOAD_FAST                'x'
             1992  LOAD_FAST                'y'
             1994  LOAD_CONST               10
             1996  BINARY_SUBTRACT  
             1998  BUILD_TUPLE_2         2 
             2000  LOAD_GLOBAL              cv2
             2002  LOAD_ATTR                FONT_HERSHEY_SIMPLEX
             2004  LOAD_CONST               0.5
             2006  LOAD_CONST               (225, 225, 0)
             2008  LOAD_CONST               2
             2010  CALL_METHOD_7         7  '7 positional arguments'
             2012  POP_TOP          

 L.1293      2014  LOAD_FAST                'barcodeData'
             2016  STORE_FAST               'identify_tag'

 L.1294      2018  LOAD_FAST                'identify_tag'
             2020  LOAD_STR                 ''
             2022  COMPARE_OP               !=
         2024_2026  POP_JUMP_IF_FALSE  1900  'to 1900'

 L.1295      2028  LOAD_STR                 'The Message is '
             2030  LOAD_FAST                'identify_tag'
             2032  BINARY_ADD       
             2034  STORE_FAST               'identify_tag'
         2036_2038  JUMP_BACK          1900  'to 1900'
             2040  POP_BLOCK        
           2042_0  COME_FROM_LOOP     1894  '1894'
         2042_2044  JUMP_FORWARD       2492  'to 2492'
           2046_0  COME_FROM          1866  '1866'

 L.1296      2046  LOAD_GLOBAL              g_tag_select
             2048  LOAD_STR                 'object'
             2050  COMPARE_OP               ==
         2052_2054  POP_JUMP_IF_FALSE  2350  'to 2350'

 L.1297      2056  LOAD_GLOBAL              np
             2058  LOAD_ATTR                expand_dims
             2060  LOAD_FAST                'frame'
             2062  LOAD_CONST               0
             2064  LOAD_CONST               ('axis',)
             2066  CALL_FUNCTION_KW_2     2  '2 total positional and keyword args'
             2068  STORE_FAST               'image_np_expanded'

 L.1298      2070  LOAD_GLOBAL              detection_graph
             2072  LOAD_METHOD              get_tensor_by_name
             2074  LOAD_STR                 'image_tensor:0'
             2076  CALL_METHOD_1         1  '1 positional argument'
             2078  STORE_FAST               'image_tensor'

 L.1299      2080  LOAD_GLOBAL              detection_graph
             2082  LOAD_METHOD              get_tensor_by_name
             2084  LOAD_STR                 'detection_boxes:0'
             2086  CALL_METHOD_1         1  '1 positional argument'
             2088  STORE_FAST               'detection_boxes'

 L.1300      2090  LOAD_GLOBAL              detection_graph
             2092  LOAD_METHOD              get_tensor_by_name
             2094  LOAD_STR                 'detection_scores:0'
             2096  CALL_METHOD_1         1  '1 positional argument'
             2098  STORE_FAST               'detection_scores'

 L.1301      2100  LOAD_GLOBAL              detection_graph
             2102  LOAD_METHOD              get_tensor_by_name
             2104  LOAD_STR                 'detection_classes:0'
             2106  CALL_METHOD_1         1  '1 positional argument'
             2108  STORE_FAST               'detection_classes'

 L.1302      2110  LOAD_GLOBAL              detection_graph
             2112  LOAD_METHOD              get_tensor_by_name
             2114  LOAD_STR                 'num_detections:0'
             2116  CALL_METHOD_1         1  '1 positional argument'
             2118  STORE_FAST               'num_detections'

 L.1305      2120  LOAD_FAST                'sess'
             2122  LOAD_ATTR                run

 L.1306      2124  LOAD_FAST                'detection_boxes'
             2126  LOAD_FAST                'detection_scores'
             2128  LOAD_FAST                'detection_classes'
             2130  LOAD_FAST                'num_detections'
             2132  BUILD_LIST_4          4 

 L.1307      2134  LOAD_FAST                'image_tensor'
             2136  LOAD_FAST                'image_np_expanded'
             2138  BUILD_MAP_1           1 
             2140  LOAD_CONST               ('feed_dict',)
             2142  CALL_FUNCTION_KW_2     2  '2 total positional and keyword args'
             2144  UNPACK_SEQUENCE_4     4 
             2146  STORE_FAST               'boxes'
             2148  STORE_FAST               'scores'
             2150  STORE_FAST               'classes'
             2152  STORE_FAST               'num'

 L.1310      2154  LOAD_GLOBAL              vis_utils
             2156  LOAD_ATTR                visualize_boxes_and_labels_on_image_array

 L.1311      2158  LOAD_FAST                'frame'

 L.1312      2160  LOAD_GLOBAL              np
             2162  LOAD_METHOD              squeeze
             2164  LOAD_FAST                'boxes'
             2166  CALL_METHOD_1         1  '1 positional argument'

 L.1313      2168  LOAD_GLOBAL              np
             2170  LOAD_METHOD              squeeze
             2172  LOAD_FAST                'classes'
             2174  CALL_METHOD_1         1  '1 positional argument'
             2176  LOAD_METHOD              astype
             2178  LOAD_GLOBAL              np
             2180  LOAD_ATTR                int32
             2182  CALL_METHOD_1         1  '1 positional argument'

 L.1314      2184  LOAD_GLOBAL              np
             2186  LOAD_METHOD              squeeze
             2188  LOAD_FAST                'scores'
             2190  CALL_METHOD_1         1  '1 positional argument'

 L.1315      2192  LOAD_GLOBAL              category_index

 L.1316      2194  LOAD_CONST               True

 L.1317      2196  LOAD_CONST               8
             2198  LOAD_CONST               ('use_normalized_coordinates', 'line_thickness')
             2200  CALL_FUNCTION_KW_7     7  '7 total positional and keyword args'
             2202  POP_TOP          

 L.1318      2204  SETUP_LOOP         2330  'to 2330'
             2206  LOAD_GLOBAL              range
             2208  LOAD_CONST               0
             2210  LOAD_CONST               10
             2212  CALL_FUNCTION_2       2  '2 positional arguments'
             2214  GET_ITER         
           2216_0  COME_FROM          2234  '2234'
             2216  FOR_ITER           2328  'to 2328'
             2218  STORE_FAST               'i'

 L.1319      2220  LOAD_FAST                'scores'
             2222  LOAD_CONST               0
             2224  BINARY_SUBSCR    
             2226  LOAD_FAST                'i'
             2228  BINARY_SUBSCR    
             2230  LOAD_CONST               0.4
             2232  COMPARE_OP               >=
         2234_2236  POP_JUMP_IF_FALSE  2216  'to 2216'

 L.1320      2238  LOAD_FAST                'i'
             2240  LOAD_CONST               0
             2242  COMPARE_OP               ==
         2244_2246  POP_JUMP_IF_FALSE  2252  'to 2252'

 L.1321      2248  LOAD_STR                 ''
             2250  STORE_FAST               'identify_tag'
           2252_0  COME_FROM          2244  '2244'

 L.1322      2252  LOAD_FAST                'identify_tag'
             2254  LOAD_STR                 ''
             2256  COMPARE_OP               ==
         2258_2260  POP_JUMP_IF_FALSE  2292  'to 2292'

 L.1323      2262  LOAD_FAST                'identify_tag'
             2264  LOAD_GLOBAL              category_index
             2266  LOAD_GLOBAL              int
             2268  LOAD_FAST                'classes'
             2270  LOAD_CONST               0
             2272  BINARY_SUBSCR    
             2274  LOAD_FAST                'i'
             2276  BINARY_SUBSCR    
             2278  CALL_FUNCTION_1       1  '1 positional argument'
             2280  BINARY_SUBSCR    
             2282  LOAD_STR                 'name'
             2284  BINARY_SUBSCR    
             2286  BINARY_ADD       
             2288  STORE_FAST               'identify_tag'
             2290  JUMP_BACK          2216  'to 2216'
           2292_0  COME_FROM          2258  '2258'

 L.1325      2292  LOAD_FAST                'identify_tag'
             2294  LOAD_STR                 ' and '
             2296  BINARY_ADD       
             2298  LOAD_GLOBAL              category_index
             2300  LOAD_GLOBAL              int
             2302  LOAD_FAST                'classes'
             2304  LOAD_CONST               0
             2306  BINARY_SUBSCR    
             2308  LOAD_FAST                'i'
             2310  BINARY_SUBSCR    
             2312  CALL_FUNCTION_1       1  '1 positional argument'
             2314  BINARY_SUBSCR    
             2316  LOAD_STR                 'name'
             2318  BINARY_SUBSCR    
             2320  BINARY_ADD       
             2322  STORE_FAST               'identify_tag'
         2324_2326  JUMP_BACK          2216  'to 2216'
             2328  POP_BLOCK        
           2330_0  COME_FROM_LOOP     2204  '2204'

 L.1326      2330  LOAD_FAST                'identify_tag'
             2332  LOAD_STR                 ''
             2334  COMPARE_OP               !=
         2336_2338  POP_JUMP_IF_FALSE  2492  'to 2492'

 L.1327      2340  LOAD_STR                 'I Find '
             2342  LOAD_FAST                'identify_tag'
             2344  BINARY_ADD       
             2346  STORE_FAST               'identify_tag'
             2348  JUMP_FORWARD       2492  'to 2492'
           2350_0  COME_FROM          2052  '2052'

 L.1328      2350  LOAD_GLOBAL              g_tag_select
             2352  LOAD_STR                 'gesture'
             2354  COMPARE_OP               ==
         2356_2358  POP_JUMP_IF_FALSE  2492  'to 2492'

 L.1331      2360  LOAD_GLOBAL              str
             2362  LOAD_GLOBAL              client_body
             2364  LOAD_METHOD              gesture
             2366  LOAD_GLOBAL              bgr8_to_jpeg
             2368  LOAD_FAST                'frame'
             2370  CALL_FUNCTION_1       1  '1 positional argument'
             2372  CALL_METHOD_1         1  '1 positional argument'
             2374  CALL_FUNCTION_1       1  '1 positional argument'
             2376  STORE_FAST               'raw'

 L.1333      2378  LOAD_GLOBAL              demjson
             2380  LOAD_METHOD              decode
             2382  LOAD_FAST                'raw'
             2384  CALL_METHOD_1         1  '1 positional argument'
             2386  STORE_FAST               'text'

 L.1335      2388  SETUP_EXCEPT       2410  'to 2410'

 L.1336      2390  LOAD_FAST                'text'
             2392  LOAD_STR                 'result'
             2394  BINARY_SUBSCR    
             2396  LOAD_CONST               0
             2398  BINARY_SUBSCR    
             2400  LOAD_STR                 'classname'
             2402  BINARY_SUBSCR    
             2404  STORE_FAST               'res'
             2406  POP_BLOCK        
             2408  JUMP_FORWARD       2444  'to 2444'
           2410_0  COME_FROM_EXCEPT   2388  '2388'

 L.1337      2410  POP_TOP          
             2412  POP_TOP          
             2414  POP_TOP          

 L.1343      2416  LOAD_GLOBAL              cv2ImgAddText
             2418  LOAD_FAST                'frame'
             2420  LOAD_STR                 'Not recognized'
             2422  LOAD_CONST               10
             2424  LOAD_CONST               30
             2426  LOAD_CONST               (0, 0, 255)
             2428  LOAD_CONST               30
             2430  CALL_FUNCTION_6       6  '6 positional arguments'
             2432  STORE_FAST               'frame'

 L.1344      2434  LOAD_STR                 'Not recognized'
             2436  STORE_FAST               'info'
             2438  POP_EXCEPT       
             2440  JUMP_FORWARD       2492  'to 2492'
             2442  END_FINALLY      
           2444_0  COME_FROM          2408  '2408'

 L.1347      2444  LOAD_GLOBAL              hand
             2446  LOAD_FAST                'res'
             2448  BINARY_SUBSCR    
             2450  STORE_FAST               'info'

 L.1350      2452  LOAD_GLOBAL              cv2ImgAddText
             2454  LOAD_FAST                'frame'
             2456  LOAD_GLOBAL              hand
             2458  LOAD_FAST                'res'
             2460  BINARY_SUBSCR    
             2462  LOAD_CONST               10
             2464  LOAD_CONST               30
             2466  LOAD_CONST               (0, 255, 0)
             2468  LOAD_CONST               30
             2470  CALL_FUNCTION_6       6  '6 positional arguments'
             2472  STORE_FAST               'frame'

 L.1353      2474  LOAD_FAST                'info'
             2476  STORE_FAST               'identify_tag'

 L.1354      2478  LOAD_FAST                'identify_tag'
             2480  LOAD_STR                 ''
             2482  COMPARE_OP               !=
         2484_2486  POP_JUMP_IF_FALSE  2492  'to 2492'

 L.1355      2488  LOAD_FAST                'identify_tag'
             2490  STORE_FAST               'identify_tag'
           2492_0  COME_FROM          2484  '2484'
           2492_1  COME_FROM          2440  '2440'
           2492_2  COME_FROM          2356  '2356'
           2492_3  COME_FROM          2348  '2348'
           2492_4  COME_FROM          2336  '2336'
           2492_5  COME_FROM          2042  '2042'

 L.1357      2492  LOAD_GLOBAL              g_tag_brodcast_switch
             2494  LOAD_STR                 'open'
             2496  COMPARE_OP               ==
         2498_2500  POP_JUMP_IF_FALSE  3728  'to 3728'

 L.1358      2502  LOAD_FAST                'identify_tag'
             2504  LOAD_STR                 ''
             2506  COMPARE_OP               !=
         2508_2510  POP_JUMP_IF_FALSE  3728  'to 3728'

 L.1359      2512  LOAD_FAST                'identify_tag'
             2514  LOAD_FAST                'last_identify_tag'
             2516  COMPARE_OP               !=
         2518_2520  POP_JUMP_IF_FALSE  3728  'to 3728'

 L.1360      2522  LOAD_GLOBAL              g_tag_select
             2524  LOAD_STR                 'object'
             2526  COMPARE_OP               ==
         2528_2530  POP_JUMP_IF_FALSE  2672  'to 2672'

 L.1361      2532  LOAD_FAST                'object_brodcast_delay'
             2534  LOAD_CONST               1
             2536  INPLACE_ADD      
             2538  STORE_FAST               'object_brodcast_delay'

 L.1362      2540  LOAD_FAST                'object_brodcast_delay'
             2542  LOAD_CONST               8
             2544  COMPARE_OP               >=
         2546_2548  POP_JUMP_IF_FALSE  2808  'to 2808'

 L.1363      2550  LOAD_GLOBAL              client
             2552  LOAD_ATTR                synthesis
             2554  LOAD_FAST                'identify_tag'

 L.1364      2556  LOAD_CONST               3
             2558  LOAD_CONST               15
             2560  LOAD_CONST               2
             2562  LOAD_CONST               ('spd', 'vol', 'per')
             2564  BUILD_CONST_KEY_MAP_3     3 
             2566  LOAD_CONST               ('text', 'options')
             2568  CALL_FUNCTION_KW_2     2  '2 total positional and keyword args'
             2570  STORE_FAST               'result'

 L.1366      2572  LOAD_GLOBAL              isinstance
             2574  LOAD_FAST                'result'
             2576  LOAD_GLOBAL              dict
             2578  CALL_FUNCTION_2       2  '2 positional arguments'
         2580_2582  POP_JUMP_IF_TRUE   2658  'to 2658'

 L.1367      2584  LOAD_GLOBAL              open
             2586  LOAD_STR                 '/home/pi/yahboom-raspblock/audio.mp3'
             2588  LOAD_STR                 'wb'
             2590  CALL_FUNCTION_2       2  '2 positional arguments'
             2592  SETUP_WITH         2650  'to 2650'
             2594  STORE_FAST               'f'

 L.1368      2596  LOAD_FAST                'f'
             2598  LOAD_METHOD              write
             2600  LOAD_FAST                'result'
             2602  CALL_METHOD_1         1  '1 positional argument'
             2604  POP_TOP          

 L.1370      2606  LOAD_GLOBAL              pygame
             2608  LOAD_ATTR                mixer
             2610  LOAD_METHOD              init
             2612  CALL_METHOD_0         0  '0 positional arguments'
             2614  POP_TOP          

 L.1371      2616  LOAD_GLOBAL              pygame
             2618  LOAD_ATTR                mixer
             2620  LOAD_ATTR                music
             2622  LOAD_METHOD              load
             2624  LOAD_STR                 '/home/pi/yahboom-raspblock/audio.mp3'
             2626  CALL_METHOD_1         1  '1 positional argument'
             2628  POP_TOP          

 L.1372      2630  LOAD_GLOBAL              pygame
             2632  LOAD_ATTR                mixer
             2634  LOAD_ATTR                music
             2636  LOAD_METHOD              play
             2638  CALL_METHOD_0         0  '0 positional arguments'
             2640  POP_TOP          

 L.1373      2642  LOAD_FAST                'identify_tag'
             2644  STORE_FAST               'last_identify_tag'
             2646  POP_BLOCK        
             2648  LOAD_CONST               None
           2650_0  COME_FROM_WITH     2592  '2592'
             2650  WITH_CLEANUP_START
             2652  WITH_CLEANUP_FINISH
             2654  END_FINALLY      
             2656  JUMP_FORWARD       2666  'to 2666'
           2658_0  COME_FROM          2580  '2580'

 L.1375      2658  LOAD_GLOBAL              print
             2660  LOAD_FAST                'result'
             2662  CALL_FUNCTION_1       1  '1 positional argument'
             2664  POP_TOP          
           2666_0  COME_FROM          2656  '2656'

 L.1376      2666  LOAD_CONST               0
             2668  STORE_FAST               'object_brodcast_delay'
             2670  JUMP_FORWARD       3728  'to 3728'
           2672_0  COME_FROM          2528  '2528'

 L.1377      2672  LOAD_GLOBAL              g_tag_select
             2674  LOAD_STR                 'qrcode'
             2676  COMPARE_OP               ==
         2678_2680  POP_JUMP_IF_TRUE   2692  'to 2692'
             2682  LOAD_GLOBAL              g_tag_select
             2684  LOAD_STR                 'gesture'
             2686  COMPARE_OP               ==
         2688_2690  POP_JUMP_IF_FALSE  3728  'to 3728'
           2692_0  COME_FROM          2678  '2678'

 L.1378      2692  LOAD_GLOBAL              client
             2694  LOAD_ATTR                synthesis
             2696  LOAD_FAST                'identify_tag'

 L.1379      2698  LOAD_CONST               3
             2700  LOAD_CONST               15
             2702  LOAD_CONST               2
             2704  LOAD_CONST               ('spd', 'vol', 'per')
             2706  BUILD_CONST_KEY_MAP_3     3 
             2708  LOAD_CONST               ('text', 'options')
             2710  CALL_FUNCTION_KW_2     2  '2 total positional and keyword args'
             2712  STORE_FAST               'result'

 L.1381      2714  LOAD_GLOBAL              isinstance
             2716  LOAD_FAST                'result'
             2718  LOAD_GLOBAL              dict
             2720  CALL_FUNCTION_2       2  '2 positional arguments'
         2722_2724  POP_JUMP_IF_TRUE   2800  'to 2800'

 L.1382      2726  LOAD_GLOBAL              open
             2728  LOAD_STR                 '/home/pi/yahboom-raspblock/audio.mp3'
             2730  LOAD_STR                 'wb'
             2732  CALL_FUNCTION_2       2  '2 positional arguments'
             2734  SETUP_WITH         2792  'to 2792'
             2736  STORE_FAST               'f'

 L.1383      2738  LOAD_FAST                'f'
             2740  LOAD_METHOD              write
             2742  LOAD_FAST                'result'
             2744  CALL_METHOD_1         1  '1 positional argument'
             2746  POP_TOP          

 L.1385      2748  LOAD_GLOBAL              pygame
             2750  LOAD_ATTR                mixer
             2752  LOAD_METHOD              init
             2754  CALL_METHOD_0         0  '0 positional arguments'
             2756  POP_TOP          

 L.1386      2758  LOAD_GLOBAL              pygame
             2760  LOAD_ATTR                mixer
             2762  LOAD_ATTR                music
             2764  LOAD_METHOD              load
             2766  LOAD_STR                 '/home/pi/yahboom-raspblock/audio.mp3'
             2768  CALL_METHOD_1         1  '1 positional argument'
             2770  POP_TOP          

 L.1387      2772  LOAD_GLOBAL              pygame
             2774  LOAD_ATTR                mixer
             2776  LOAD_ATTR                music
             2778  LOAD_METHOD              play
             2780  CALL_METHOD_0         0  '0 positional arguments'
             2782  POP_TOP          

 L.1388      2784  LOAD_FAST                'identify_tag'
             2786  STORE_FAST               'last_identify_tag'
             2788  POP_BLOCK        
             2790  LOAD_CONST               None
           2792_0  COME_FROM_WITH     2734  '2734'
             2792  WITH_CLEANUP_START
             2794  WITH_CLEANUP_FINISH
             2796  END_FINALLY      
             2798  JUMP_FORWARD       3728  'to 3728'
           2800_0  COME_FROM          2722  '2722'

 L.1390      2800  LOAD_GLOBAL              print
             2802  LOAD_FAST                'result'
             2804  CALL_FUNCTION_1       1  '1 positional argument'
             2806  POP_TOP          
           2808_0  COME_FROM          2546  '2546'
         2808_2810  JUMP_FORWARD       3728  'to 3728'
           2812_0  COME_FROM          1846  '1846'

 L.1391      2812  LOAD_GLOBAL              g_mode
             2814  LOAD_STR                 'auto_drive'
             2816  COMPARE_OP               ==
         2818_2820  POP_JUMP_IF_FALSE  3728  'to 3728'

 L.1392      2822  LOAD_GLOBAL              cv2
             2824  LOAD_METHOD              resize
             2826  LOAD_FAST                'frame'
             2828  LOAD_CONST               (320, 240)
             2830  CALL_METHOD_2         2  '2 positional arguments'
             2832  STORE_FAST               'frame'

 L.1394      2834  LOAD_GLOBAL              cv2
             2836  LOAD_METHOD              warpPerspective
             2838  LOAD_FAST                'frame'
             2840  LOAD_FAST                'matAffine'
             2842  LOAD_CONST               (320, 240)
             2844  CALL_METHOD_3         3  '3 positional arguments'
             2846  STORE_FAST               'dst'

 L.1398      2848  LOAD_FAST                'pts'
             2850  LOAD_METHOD              reshape
             2852  LOAD_CONST               (-1, 1, 2)
             2854  CALL_METHOD_1         1  '1 positional argument'
             2856  STORE_FAST               'pts'

 L.1399      2858  LOAD_GLOBAL              cv2
             2860  LOAD_METHOD              polylines
             2862  LOAD_FAST                'frame'
             2864  LOAD_FAST                'pts'
             2866  BUILD_LIST_1          1 
             2868  LOAD_CONST               True
             2870  LOAD_CONST               (255, 0, 0)
             2872  LOAD_CONST               3
             2874  CALL_METHOD_5         5  '5 positional arguments'
             2876  POP_TOP          

 L.1401      2878  LOAD_GLOBAL              cv2
             2880  LOAD_METHOD              cvtColor
             2882  LOAD_FAST                'dst'
             2884  LOAD_GLOBAL              cv2
             2886  LOAD_ATTR                COLOR_RGB2GRAY
             2888  CALL_METHOD_2         2  '2 positional arguments'
             2890  STORE_FAST               'dst_gray'

 L.1402      2892  LOAD_GLOBAL              cv2
             2894  LOAD_METHOD              threshold
             2896  LOAD_FAST                'dst_gray'
             2898  LOAD_CONST               128
             2900  LOAD_CONST               255
             2902  LOAD_GLOBAL              cv2
             2904  LOAD_ATTR                THRESH_BINARY
             2906  CALL_METHOD_4         4  '4 positional arguments'
             2908  UNPACK_SEQUENCE_2     2 
             2910  STORE_FAST               'dst_retval'
             2912  STORE_FAST               'dst_binaryzation'

 L.1403      2914  LOAD_GLOBAL              cv2
             2916  LOAD_ATTR                erode
             2918  LOAD_FAST                'dst_binaryzation'
             2920  LOAD_CONST               None
             2922  LOAD_CONST               1
             2924  LOAD_CONST               ('iterations',)
             2926  CALL_FUNCTION_KW_3     3  '3 total positional and keyword args'
             2928  STORE_FAST               'dst_binaryzation'

 L.1404      2930  LOAD_GLOBAL              np
             2932  LOAD_ATTR                sum
             2934  LOAD_FAST                'dst_binaryzation'
             2936  LOAD_FAST                'dst_binaryzation'
             2938  LOAD_ATTR                shape
             2940  LOAD_CONST               0
             2942  BINARY_SUBSCR    
             2944  LOAD_CONST               2
             2946  BINARY_FLOOR_DIVIDE
             2948  LOAD_CONST               None
             2950  BUILD_SLICE_2         2 
             2952  LOAD_CONST               None
             2954  LOAD_CONST               None
             2956  BUILD_SLICE_2         2 
             2958  BUILD_TUPLE_2         2 
             2960  BINARY_SUBSCR    
             2962  LOAD_CONST               0
             2964  LOAD_CONST               ('axis',)
             2966  CALL_FUNCTION_KW_2     2  '2 total positional and keyword args'
             2968  STORE_FAST               'histogram'

 L.1405      2970  LOAD_GLOBAL              np
             2972  LOAD_METHOD              int
             2974  LOAD_FAST                'histogram'
             2976  LOAD_ATTR                shape
             2978  LOAD_CONST               0
             2980  BINARY_SUBSCR    
             2982  LOAD_CONST               2
             2984  BINARY_TRUE_DIVIDE
             2986  CALL_METHOD_1         1  '1 positional argument'
             2988  STORE_FAST               'midpoint'

 L.1412      2990  LOAD_GLOBAL              np
             2992  LOAD_ATTR                argmin
             2994  LOAD_FAST                'histogram'
             2996  LOAD_CONST               None
             2998  LOAD_FAST                'midpoint'
             3000  BUILD_SLICE_2         2 
             3002  BINARY_SUBSCR    
             3004  LOAD_CONST               0
             3006  LOAD_CONST               ('axis',)
             3008  CALL_FUNCTION_KW_2     2  '2 total positional and keyword args'
             3010  LOAD_CONST               5
             3012  BINARY_ADD       
             3014  STORE_FAST               'leftx_base'

 L.1413      3016  LOAD_GLOBAL              np
             3018  LOAD_ATTR                argmin
             3020  LOAD_FAST                'histogram'
             3022  LOAD_FAST                'midpoint'
             3024  LOAD_CONST               None
             3026  BUILD_SLICE_2         2 
             3028  BINARY_SUBSCR    
             3030  LOAD_CONST               0
             3032  LOAD_CONST               ('axis',)
             3034  CALL_FUNCTION_KW_2     2  '2 total positional and keyword args'
             3036  LOAD_FAST                'midpoint'
             3038  BINARY_ADD       
             3040  LOAD_CONST               5
             3042  BINARY_ADD       
             3044  STORE_FAST               'rightx_base'

 L.1429      3046  LOAD_FAST                'leftx_base'
             3048  LOAD_CONST               10
             3050  COMPARE_OP               <
         3052_3054  POP_JUMP_IF_FALSE  3060  'to 3060'

 L.1430      3056  LOAD_CONST               10
             3058  STORE_FAST               'leftx_base'
           3060_0  COME_FROM          3052  '3052'

 L.1431      3060  LOAD_FAST                'rightx_base'
             3062  LOAD_CONST               300
             3064  COMPARE_OP               >
         3066_3068  POP_JUMP_IF_FALSE  3074  'to 3074'

 L.1432      3070  LOAD_CONST               300
             3072  STORE_FAST               'rightx_base'
           3074_0  COME_FROM          3066  '3066'

 L.1433      3074  LOAD_FAST                'leftx_base'
             3076  LOAD_CONST               140
             3078  COMPARE_OP               >
         3080_3082  POP_JUMP_IF_TRUE   3098  'to 3098'
             3084  LOAD_FAST                'rightx_base'
             3086  LOAD_FAST                'leftx_base'
             3088  BINARY_SUBTRACT  
             3090  LOAD_CONST               50
             3092  COMPARE_OP               <
         3094_3096  POP_JUMP_IF_FALSE  3102  'to 3102'
           3098_0  COME_FROM          3080  '3080'

 L.1434      3098  LOAD_CONST               10
             3100  STORE_FAST               'leftx_base'
           3102_0  COME_FROM          3094  '3094'

 L.1435      3102  LOAD_FAST                'rightx_base'
             3104  LOAD_CONST               159
             3106  COMPARE_OP               <
         3108_3110  POP_JUMP_IF_TRUE   3126  'to 3126'
             3112  LOAD_FAST                'rightx_base'
             3114  LOAD_FAST                'leftx_base'
             3116  BINARY_SUBTRACT  
             3118  LOAD_CONST               50
             3120  COMPARE_OP               <
         3122_3124  POP_JUMP_IF_FALSE  3130  'to 3130'
           3126_0  COME_FROM          3108  '3108'

 L.1436      3126  LOAD_CONST               300
             3128  STORE_FAST               'rightx_base'
           3130_0  COME_FROM          3122  '3122'

 L.1438      3130  LOAD_GLOBAL              np
             3132  LOAD_ATTR                sum
             3134  LOAD_FAST                'dst_binaryzation'
             3136  LOAD_FAST                'dst_binaryzation'
             3138  LOAD_ATTR                shape
             3140  LOAD_CONST               0
             3142  BINARY_SUBSCR    
             3144  LOAD_CONST               2
             3146  BINARY_FLOOR_DIVIDE
             3148  LOAD_CONST               None
             3150  BUILD_SLICE_2         2 
             3152  LOAD_CONST               None
             3154  LOAD_CONST               None
             3156  BUILD_SLICE_2         2 
             3158  BUILD_TUPLE_2         2 
             3160  BINARY_SUBSCR    
             3162  LOAD_CONST               0
             3164  LOAD_CONST               ('axis',)
             3166  CALL_FUNCTION_KW_2     2  '2 total positional and keyword args'
             3168  STORE_FAST               'histogram'

 L.1439      3170  LOAD_GLOBAL              cv2
             3172  LOAD_METHOD              cvtColor
             3174  LOAD_FAST                'dst_binaryzation'
             3176  LOAD_GLOBAL              cv2
             3178  LOAD_ATTR                COLOR_GRAY2RGB
             3180  CALL_METHOD_2         2  '2 positional arguments'
             3182  STORE_FAST               'dst_binaryzation'

 L.1440      3184  LOAD_GLOBAL              cv2
             3186  LOAD_METHOD              line
             3188  LOAD_FAST                'dst_binaryzation'
             3190  LOAD_CONST               (154, 0)
             3192  LOAD_CONST               (154, 240)
             3194  LOAD_CONST               (255, 0, 255)
             3196  LOAD_CONST               2
             3198  CALL_METHOD_5         5  '5 positional arguments'
             3200  POP_TOP          

 L.1441      3202  LOAD_GLOBAL              int
             3204  LOAD_FAST                'leftx_base'
             3206  LOAD_FAST                'rightx_base'
             3208  BINARY_ADD       
             3210  LOAD_CONST               2
             3212  BINARY_TRUE_DIVIDE
             3214  CALL_FUNCTION_1       1  '1 positional argument'
             3216  STORE_FAST               'lane_center'

 L.1442      3218  LOAD_GLOBAL              cv2
             3220  LOAD_METHOD              line
             3222  LOAD_FAST                'dst_binaryzation'
             3224  LOAD_FAST                'leftx_base'
             3226  LOAD_CONST               0
             3228  BUILD_TUPLE_2         2 
             3230  LOAD_FAST                'leftx_base'
             3232  LOAD_CONST               240
             3234  BUILD_TUPLE_2         2 
             3236  LOAD_CONST               (0, 255, 0)
             3238  LOAD_CONST               2
             3240  CALL_METHOD_5         5  '5 positional arguments'
             3242  POP_TOP          

 L.1443      3244  LOAD_GLOBAL              cv2
             3246  LOAD_METHOD              line
             3248  LOAD_FAST                'dst_binaryzation'
             3250  LOAD_FAST                'rightx_base'
             3252  LOAD_CONST               0
             3254  BUILD_TUPLE_2         2 
             3256  LOAD_FAST                'rightx_base'
             3258  LOAD_CONST               240
             3260  BUILD_TUPLE_2         2 
             3262  LOAD_CONST               (0, 255, 0)
             3264  LOAD_CONST               2
             3266  CALL_METHOD_5         5  '5 positional arguments'
             3268  POP_TOP          

 L.1444      3270  LOAD_GLOBAL              cv2
             3272  LOAD_METHOD              line
             3274  LOAD_FAST                'dst_binaryzation'
             3276  LOAD_FAST                'lane_center'
             3278  LOAD_CONST               0
             3280  BUILD_TUPLE_2         2 
             3282  LOAD_FAST                'lane_center'
             3284  LOAD_CONST               240
             3286  BUILD_TUPLE_2         2 
             3288  LOAD_CONST               (255, 0, 0)
             3290  LOAD_CONST               2
             3292  CALL_METHOD_5         5  '5 positional arguments'
             3294  POP_TOP          

 L.1445      3296  LOAD_CONST               154
             3298  LOAD_FAST                'lane_center'
             3300  BINARY_SUBTRACT  
             3302  STORE_FAST               'Bias'

 L.1448      3304  LOAD_FAST                'Bias'
             3306  LOAD_CONST               30
             3308  COMPARE_OP               >
         3310_3312  POP_JUMP_IF_FALSE  3320  'to 3320'

 L.1449      3314  LOAD_CONST               30
             3316  STORE_FAST               'Bias'
             3318  JUMP_FORWARD       3334  'to 3334'
           3320_0  COME_FROM          3310  '3310'

 L.1450      3320  LOAD_FAST                'Bias'
             3322  LOAD_CONST               -30
             3324  COMPARE_OP               <
         3326_3328  POP_JUMP_IF_FALSE  3334  'to 3334'

 L.1451      3330  LOAD_CONST               -30
             3332  STORE_FAST               'Bias'
           3334_0  COME_FROM          3326  '3326'
           3334_1  COME_FROM          3318  '3318'

 L.1454      3334  LOAD_FAST                'Bias'
             3336  LOAD_FAST                'Z_axis_pid'
             3338  STORE_ATTR               SystemOutput

 L.1455      3340  LOAD_FAST                'Z_axis_pid'
             3342  LOAD_METHOD              SetStepSignal
             3344  LOAD_CONST               0
             3346  CALL_METHOD_1         1  '1 positional argument'
             3348  POP_TOP          

 L.1456      3350  LOAD_FAST                'Z_axis_pid'
             3352  LOAD_METHOD              SetInertiaTime
             3354  LOAD_CONST               0.5
             3356  LOAD_CONST               0.2
             3358  CALL_METHOD_2         2  '2 positional arguments'
             3360  POP_TOP          

 L.1458      3362  LOAD_FAST                'Z_axis_pid'
             3364  LOAD_ATTR                SystemOutput
             3366  LOAD_CONST               30
             3368  COMPARE_OP               >
         3370_3372  POP_JUMP_IF_FALSE  3382  'to 3382'

 L.1459      3374  LOAD_CONST               30
             3376  LOAD_FAST                'Z_axis_pid'
             3378  STORE_ATTR               SystemOutput
             3380  JUMP_FORWARD       3400  'to 3400'
           3382_0  COME_FROM          3370  '3370'

 L.1460      3382  LOAD_FAST                'Z_axis_pid'
             3384  LOAD_ATTR                SystemOutput
             3386  LOAD_CONST               -30
             3388  COMPARE_OP               <
         3390_3392  POP_JUMP_IF_FALSE  3400  'to 3400'

 L.1461      3394  LOAD_CONST               -30
             3396  LOAD_FAST                'Z_axis_pid'
             3398  STORE_ATTR               SystemOutput
           3400_0  COME_FROM          3390  '3390'
           3400_1  COME_FROM          3380  '3380'

 L.1467      3400  LOAD_GLOBAL              g_auto_drive_switch
             3402  LOAD_STR                 'open'
             3404  COMPARE_OP               ==
         3406_3408  POP_JUMP_IF_FALSE  3430  'to 3430'

 L.1469      3410  LOAD_GLOBAL              robot
             3412  LOAD_METHOD              Speed_axis_control
             3414  LOAD_CONST               0
             3416  LOAD_CONST               5
             3418  LOAD_GLOBAL              int
             3420  LOAD_FAST                'Z_axis_pid'
             3422  LOAD_ATTR                SystemOutput
             3424  CALL_FUNCTION_1       1  '1 positional argument'
             3426  CALL_METHOD_3         3  '3 positional arguments'
             3428  POP_TOP          
           3430_0  COME_FROM          3406  '3406'

 L.1482      3430  LOAD_GLOBAL              g_drive_view_switch
             3432  LOAD_CONST               0
             3434  COMPARE_OP               ==
         3436_3438  POP_JUMP_IF_FALSE  3494  'to 3494'

 L.1483      3440  LOAD_GLOBAL              cv2
             3442  LOAD_METHOD              putText
             3444  LOAD_FAST                'frame'
             3446  LOAD_STR                 'FPS:  '
             3448  LOAD_GLOBAL              str
             3450  LOAD_GLOBAL              int
             3452  LOAD_FAST                'mfps'
             3454  CALL_FUNCTION_1       1  '1 positional argument'
             3456  CALL_FUNCTION_1       1  '1 positional argument'
             3458  BINARY_ADD       
             3460  LOAD_CONST               (10, 15)
             3462  LOAD_GLOBAL              cv2
             3464  LOAD_ATTR                FONT_HERSHEY_SIMPLEX
             3466  LOAD_CONST               0.5
             3468  LOAD_CONST               (0, 255, 255)
             3470  LOAD_CONST               1
             3472  CALL_METHOD_7         7  '7 positional arguments'
             3474  POP_TOP          

 L.1484      3476  LOAD_GLOBAL              cv2
             3478  LOAD_METHOD              imencode
             3480  LOAD_STR                 '.jpg'
             3482  LOAD_FAST                'frame'
             3484  CALL_METHOD_2         2  '2 positional arguments'
             3486  LOAD_CONST               1
             3488  BINARY_SUBSCR    
             3490  STORE_FAST               'imgencode'
             3492  JUMP_FORWARD       3728  'to 3728'
           3494_0  COME_FROM          3436  '3436'

 L.1485      3494  LOAD_GLOBAL              g_drive_view_switch
             3496  LOAD_CONST               1
             3498  COMPARE_OP               ==
         3500_3502  POP_JUMP_IF_FALSE  3558  'to 3558'

 L.1486      3504  LOAD_GLOBAL              cv2
             3506  LOAD_METHOD              putText
             3508  LOAD_FAST                'dst'
             3510  LOAD_STR                 'FPS:  '
             3512  LOAD_GLOBAL              str
             3514  LOAD_GLOBAL              int
             3516  LOAD_FAST                'mfps'
             3518  CALL_FUNCTION_1       1  '1 positional argument'
             3520  CALL_FUNCTION_1       1  '1 positional argument'
             3522  BINARY_ADD       
             3524  LOAD_CONST               (10, 15)
             3526  LOAD_GLOBAL              cv2
             3528  LOAD_ATTR                FONT_HERSHEY_SIMPLEX
             3530  LOAD_CONST               0.5
             3532  LOAD_CONST               (0, 255, 255)
             3534  LOAD_CONST               1
             3536  CALL_METHOD_7         7  '7 positional arguments'
             3538  POP_TOP          

 L.1487      3540  LOAD_GLOBAL              cv2
             3542  LOAD_METHOD              imencode
             3544  LOAD_STR                 '.jpg'
             3546  LOAD_FAST                'dst'
             3548  CALL_METHOD_2         2  '2 positional arguments'
             3550  LOAD_CONST               1
             3552  BINARY_SUBSCR    
             3554  STORE_FAST               'imgencode'
             3556  JUMP_FORWARD       3728  'to 3728'
           3558_0  COME_FROM          3500  '3500'

 L.1488      3558  LOAD_GLOBAL              g_drive_view_switch
             3560  LOAD_CONST               2
             3562  COMPARE_OP               ==
         3564_3566  POP_JUMP_IF_FALSE  3728  'to 3728'

 L.1489      3568  LOAD_GLOBAL              cv2
             3570  LOAD_METHOD              putText
             3572  LOAD_FAST                'dst_binaryzation'
             3574  LOAD_STR                 'FPS:  '
             3576  LOAD_GLOBAL              str
             3578  LOAD_GLOBAL              int
             3580  LOAD_FAST                'mfps'
             3582  CALL_FUNCTION_1       1  '1 positional argument'
             3584  CALL_FUNCTION_1       1  '1 positional argument'
             3586  BINARY_ADD       
           3588_0  COME_FROM          2670  '2670'
             3588  LOAD_CONST               (10, 15)
             3590  LOAD_GLOBAL              cv2
             3592  LOAD_ATTR                FONT_HERSHEY_SIMPLEX
             3594  LOAD_CONST               0.5
             3596  LOAD_CONST               (0, 255, 255)
             3598  LOAD_CONST               2
             3600  CALL_METHOD_7         7  '7 positional arguments'
             3602  POP_TOP          

 L.1490      3604  LOAD_GLOBAL              cv2
             3606  LOAD_METHOD              putText
             3608  LOAD_FAST                'dst_binaryzation'
             3610  LOAD_STR                 'Bias: '
             3612  LOAD_GLOBAL              str
             3614  LOAD_GLOBAL              int
             3616  LOAD_FAST                'Bias'
             3618  CALL_FUNCTION_1       1  '1 positional argument'
             3620  CALL_FUNCTION_1       1  '1 positional argument'
             3622  BINARY_ADD       
             3624  LOAD_CONST               (10, 35)
             3626  LOAD_GLOBAL              cv2
             3628  LOAD_ATTR                FONT_HERSHEY_SIMPLEX
             3630  LOAD_CONST               0.5
             3632  LOAD_CONST               (0, 255, 255)
             3634  LOAD_CONST               2
             3636  CALL_METHOD_7         7  '7 positional arguments'
             3638  POP_TOP          

 L.1492      3640  LOAD_GLOBAL              cv2
             3642  LOAD_METHOD              putText
             3644  LOAD_FAST                'dst_binaryzation'
             3646  LOAD_STR                 'L_peak: '
             3648  LOAD_GLOBAL              str
             3650  LOAD_GLOBAL              int
             3652  LOAD_FAST                'leftx_base'
             3654  CALL_FUNCTION_1       1  '1 positional argument'
             3656  CALL_FUNCTION_1       1  '1 positional argument'
             3658  BINARY_ADD       
             3660  LOAD_CONST               (10, 75)
             3662  LOAD_GLOBAL              cv2
             3664  LOAD_ATTR                FONT_HERSHEY_SIMPLEX
             3666  LOAD_CONST               0.5
             3668  LOAD_CONST               (0, 255, 255)
             3670  LOAD_CONST               2
             3672  CALL_METHOD_7         7  '7 positional arguments'
             3674  POP_TOP          

 L.1493      3676  LOAD_GLOBAL              cv2
             3678  LOAD_METHOD              putText
             3680  LOAD_FAST                'dst_binaryzation'
             3682  LOAD_STR                 'R_peak: '
             3684  LOAD_GLOBAL              str
             3686  LOAD_GLOBAL              int
             3688  LOAD_FAST                'rightx_base'
             3690  CALL_FUNCTION_1       1  '1 positional argument'
             3692  CALL_FUNCTION_1       1  '1 positional argument'
             3694  BINARY_ADD       
             3696  LOAD_CONST               (10, 95)
             3698  LOAD_GLOBAL              cv2
             3700  LOAD_ATTR                FONT_HERSHEY_SIMPLEX
             3702  LOAD_CONST               0.5
             3704  LOAD_CONST               (0, 255, 255)
             3706  LOAD_CONST               2
             3708  CALL_METHOD_7         7  '7 positional arguments'
             3710  POP_TOP          

 L.1494      3712  LOAD_GLOBAL              cv2
             3714  LOAD_METHOD              imencode
           3716_0  COME_FROM          2798  '2798'
             3716  LOAD_STR                 '.jpg'
             3718  LOAD_FAST                'dst_binaryzation'
             3720  CALL_METHOD_2         2  '2 positional arguments'
             3722  LOAD_CONST               1
             3724  BINARY_SUBSCR    
             3726  STORE_FAST               'imgencode'
           3728_0  COME_FROM          3564  '3564'
           3728_1  COME_FROM          3556  '3556'
           3728_2  COME_FROM          3492  '3492'
           3728_3  COME_FROM          2818  '2818'
           3728_4  COME_FROM          2808  '2808'
           3728_5  COME_FROM          2688  '2688'
           3728_6  COME_FROM          2518  '2518'
           3728_7  COME_FROM          2508  '2508'
           3728_8  COME_FROM          2498  '2498'
           3728_9  COME_FROM          1856  '1856'
          3728_10  COME_FROM          1836  '1836'
          3728_11  COME_FROM          1542  '1542'

 L.1520      3728  LOAD_GLOBAL              g_mode
             3730  LOAD_STR                 'auto_drive'
             3732  COMPARE_OP               !=
         3734_3736  POP_JUMP_IF_FALSE  3790  'to 3790'

 L.1521      3738  LOAD_GLOBAL              cv2
             3740  LOAD_METHOD              putText
             3742  LOAD_FAST                'frame'
             3744  LOAD_STR                 'FPS:  '
             3746  LOAD_GLOBAL              str
             3748  LOAD_GLOBAL              int
             3750  LOAD_FAST                'mfps'
             3752  CALL_FUNCTION_1       1  '1 positional argument'
             3754  CALL_FUNCTION_1       1  '1 positional argument'
             3756  BINARY_ADD       
             3758  LOAD_CONST               (10, 20)
             3760  LOAD_GLOBAL              cv2
             3762  LOAD_ATTR                FONT_HERSHEY_SIMPLEX
             3764  LOAD_CONST               0.5
             3766  LOAD_CONST               (0, 255, 255)
             3768  LOAD_CONST               2
             3770  CALL_METHOD_7         7  '7 positional arguments'
             3772  POP_TOP          

 L.1522      3774  LOAD_GLOBAL              cv2
             3776  LOAD_METHOD              imencode
             3778  LOAD_STR                 '.jpg'
             3780  LOAD_FAST                'frame'
             3782  CALL_METHOD_2         2  '2 positional arguments'
             3784  LOAD_CONST               1
             3786  BINARY_SUBSCR    
             3788  STORE_FAST               'imgencode'
           3790_0  COME_FROM          3734  '3734'

 L.1524      3790  LOAD_FAST                'imgencode'
             3792  LOAD_METHOD              tostring
             3794  CALL_METHOD_0         0  '0 positional arguments'
             3796  STORE_FAST               'imgencode'

 L.1526      3798  LOAD_CONST               b'--frame\r\nContent-Type: image/jpeg\r\n\r\n'
             3800  LOAD_FAST                'imgencode'
             3802  BINARY_ADD       
             3804  LOAD_CONST               b'\r\n'
             3806  BINARY_ADD       
             3808  YIELD_VALUE      
             3810  POP_TOP          

 L.1530      3812  LOAD_GLOBAL              time
             3814  LOAD_METHOD              sleep
             3816  LOAD_CONST               0.006
             3818  CALL_METHOD_1         1  '1 positional argument'
             3820  POP_TOP          
         3822_3824  JUMP_BACK           576  'to 576'
             3826  POP_BLOCK        
           3828_0  COME_FROM_LOOP      572  '572'

 L.1531      3828  DELETE_FAST              'camera'

 L.1532      3830  LOAD_GLOBAL              robot
             3832  LOAD_METHOD              BoardData_Get
             3834  LOAD_CONST               9
             3836  CALL_METHOD_1         1  '1 positional argument'
             3838  POP_TOP          

Parse error at or near `COME_FROM' instruction at offset 3588_0


def getip():
    try:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('www.baidu.com', 0))
            ip = s.getsockname()[0]
        except:
            ip = 'x.x.x.x'

    finally:
        s.close()

    return ip


if __name__ == '__main__':
    while True:
        try:
            ip = getip()
            print(ip)
            if ip == 'x.x.x.x':
                result = client.synthesis('Not connected to WIFI, please wait！', 'zh', 1, {'spd':3,  'vol':1,  'per':3})
                if not isinstance(result, dict):
                    with open('audio.mp3', 'wb') as (f):
                        f.write(result)
                        pygame.mixer.init()
                        pygame.mixer.music.load('./audio.mp3')
                        pygame.mixer.music.play()
                        time.sleep(5)
                        pygame.mixer.init()
                        pygame.mixer.music.load('./audio.mp3')
                        pygame.mixer.music.play()
                        time.sleep(5)
                        break
                else:
                    print(result)
                continue
            if ip != 'x.x.x.x':
                result = client.synthesis('IP address is ' + ip, 'zh', 1, {'spd':3,  'vol':30,  'per':3})
                if not isinstance(result, dict):
                    with open('audio.mp3', 'wb') as (f):
                        f.write(result)
                        pygame.mixer.init()
                        pygame.mixer.music.load('./audio.mp3')
                        pygame.mixer.music.play()
                        time.sleep(10)
                        pygame.mixer.init()
                        pygame.mixer.music.load('./audio.mp3')
                        pygame.mixer.music.play()
                        time.sleep(10)
                        break
                else:
                    print(result)
        except Exception:
            raise

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
    app.run(host='0.0.0.0', port=6001, debug=False, use_reloader=False)
# global Max_speed_XY ## Warning: Unused global
# global Max_speed_Z ## Warning: Unused global
# global Position_disp_X ## Warning: Unused global
# global Position_disp_Y ## Warning: Unused global
# global Position_disp_Z ## Warning: Unused global
# global Speed_WheelA ## Warning: Unused global
# global Speed_WheelB ## Warning: Unused global
# global Speed_WheelC ## Warning: Unused global
# global Speed_WheelD ## Warning: Unused global
# global Speed_axis_X ## Warning: Unused global
# global Speed_axis_Y ## Warning: Unused global
# global Speed_axis_Z ## Warning: Unused global
# global color_lower ## Warning: Unused global
# global color_upper ## Warning: Unused global
# global g_Position_update ## Warning: Unused global
# global g_auto_drive_switch ## Warning: Unused global
# global g_drive_view_switch ## Warning: Unused global
# global g_mode ## Warning: Unused global
# global g_presentation_mode ## Warning: Unused global
# global g_robot_motion_mode ## Warning: Unused global
# global g_servormode ## Warning: Unused global
# global g_tag_brodcast_switch ## Warning: Unused global
# global g_tag_identify_switch ## Warning: Unused global
# global g_tag_select ## Warning: Unused global
# global g_target_mode ## Warning: Unused global
# global g_z_state ## Warning: Unused global
# global meanshift_X ## Warning: Unused global
# global meanshift_Y ## Warning: Unused global
# global meanshift_high ## Warning: Unused global
# global meanshift_update_flag ## Warning: Unused global
# global meanshift_width ## Warning: Unused global
# global target_valuex ## Warning: Unused global
# global target_valuey ## Warning: Unused global