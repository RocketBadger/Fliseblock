#!/usr/bin/env python2

# for get ip
import socket, time
import pygame 
from aip import AipSpeech


""" Voice technology APPID AK SK """
SpeechAPP_ID = '17852430'
SpeechAPI_KEY ='eGeO4iQGAjHCrzBTYd1uvTtf'
SpeechSECRET_KEY = 'Cn1EVsUngZDbRLv4OxAFrDHSo8PsvFVP'


Speechclient = AipSpeech(SpeechAPP_ID, SpeechAPI_KEY, SpeechSECRET_KEY)

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

if __name__ == "__main__":
    while(1):
        try:
            ip = getip()
            print(ip)
            if(ip == "x.x.x.x"):
                result = Speechclient.synthesis("Not connected to WIFI, please wait！", 'zh', 1, {'spd':3, 'vol' : 1, 'per' : 3} )

                #Write synthesized speech to file
                if not isinstance(result,dict):
                    with open('audio.mp3','wb') as f:
                        f.write(result)
                        #We use the Raspberry Pi own pygame
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
            if(ip != "x.x.x.x"):
                #result = Speechclient.synthesis(text = ip, 'zh', 1, options={'spd':3,'vol':9,'per':2,})  
                result = Speechclient.synthesis("IP address is " + ip, 'zh', 1, {'spd':3, 'vol' : 30, 'per' : 3} ) # English
                #result = Speechclient.synthesis("IP地址是：" + ip, 'zh', 1, {'spd':3, 'vol' : 1, 'per' : 3} ) # Chinese
                #Write synthesized speech to file
                if not isinstance(result,dict):
                    with open('audio.mp3','wb') as f:
                        f.write(result)
                        #We use the Raspberry Pi own pygame
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
