import io
import picamera
#import logging
from threading import Condition

import os, sys
from time import sleep
import time
from fractions import Fraction
from subprocess import check_output
#from PIL import Image

import pygame
#pigame
from pygame.locals import *
from gpiozero import Button

button1 = Button(17)
button2 = Button(22)
button3 = Button(23)
button4 = Button(27)

os.putenv('SDL_VIDEODRV','fbcon')
os.putenv('SDL_FBDEV', '/dev/fb1')
#os.putenv('SDL_MOUSEDRV','dummy')
#os.putenv('SDL_MOUSEDEV','/dev/null')
os.putenv('DISPLAY','')

class optionList():
    def __init__(self,values,startindex):
     self.list=values
     self.position=startindex
    def currentValue(self):
        return self.list[self.position]
    def nextValue(self):
     if self.position+1==len(self.list):
         self.position=0
     else:
         self.position=self.position+1
     return self.list[self.position]

class StreamingOutput(object):
   def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()
        self.screenon=True
   def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)
   
   def screen(self,thisCamera,thisScreen):
        #with self.screenon:
            with self.condition:
                         self.condition.wait()
                         frame = output.frame
             
            text_surface = headerfont.render(thisCamera.cameraActions.currentValue() + ": " + getattr(thisCamera,thisCamera.cameraActions.currentValue() + "Values").currentValue(), True, WHITE)
            text_surface2 = headerfont.render(check_output(['hostname', '-I']).decode('utf-8').split(" ")[0],True,WHITE)
                
            rect = text_surface.get_rect(center=(50,10))
            
            try:
             thisframe=pygame.image.load(io.BytesIO(frame),'JPEG')
            except pygame.error:
             print(pygame.get_error())
            thisScreen.blit(thisframe,(0,0))
            thisScreen.blit(text_surface, (5,5))
            thisScreen.blit(text_surface2, (5,225))
            pygame.display.update()
            #pitft.update()   

class AstroPhotography(object):

    def __init__(self):
        self.cameraActions=optionList(["SetISO","SetBrightness","SetZoom"],0)
        self.SetISOValues=optionList(["100","200","400","800"],0)
        self.SetBrightnessValues=optionList(["50","60","70","80","90"],0)
        self.SetZoomValues=optionList(["0","2","4"],0)
    
    def TakePhoto(self,darkframe,frames):
     rootDir=os.path.join(os.path.dirname(os.path.abspath(__file__)),'Images/Images')
     t = time.localtime()
     datestamp = time.strftime('%b-%d-%Y', t)
     timestamp = time.strftime('%b-%d-%Y_%H:%M:%S', t)
     os.makedirs(rootDir + datestamp, exist_ok=True)
     if darkframe=="True":
         fileName="DarkFrame"
     else:
         fileName="AstroShot"
     totalFrames=int(frames)    
     #camera.framerate = Fraction(1, 6)
     #camera.shutter_speed = 6000000
     #camera.exposure_mode = 'off'
     #camera.iso=100
     print('Called TakePhoto')
     for i in range(1,totalFrames+1,1):
      sleep(5)
      if totalFrames>1:
         camera.capture(rootDir + datestamp + '/' + fileName + timestamp + 'Frame' + str(i) + '.jpg')
      else:
         camera.capture(rootDir + datestamp + '/' + fileName + timestamp + '.jpg')
      sleep(10)
     return b'Capturing video'
    
    def captureVideo(self):
     rootDir=os.path.join(os.path.dirname(os.path.abspath(__file__)),'Images/Images')
     t = time.localtime()
     datestamp = time.strftime('%b-%d-%Y', t)
     timestamp = time.strftime('%b-%d-%Y_%H:%M:%S', t)
     os.makedirs(rootDir + datestamp, exist_ok=True)
     #camera.exposure_mode = 'off'
     
     #camera.wait_recording(20)
     #output.buffer.copy_to(rootDir + datestamp + '/AstroShot' + timestamp +'.mjpeg',first_frame=None)
     #camera.exposure_mode = 'auto'
     camera.start_recording(rootDir + datestamp + '/AstroShot' + timestamp +'.h264',format='h264',resize=(1640,1232))
     camera.wait_recording(20)
     camera.stop_recording(splitter_port=1)
     return b'Capturing video'
     
    
    def SetISO(self,value):
     camera.iso=int(value)
     print(camera.iso)
     return b'Setting ISO Value'
    
    def SetBrightness(self,value):
     camera.brightness=int(value)
     print(camera.brightness)
     return b'Setting ISO Value'

    
    def SetZoom(self,value):
     if int(value)==0:
         zoomMe=[0,0,1,1]
     elif int(value)==2:
         zoomMe=[0.25,0.25,0.5,0.5]
     elif int(value)==4:
         zoomMe=[0.375,0.375,0.25,0.25]
     else:
         zoomMe=[0,0,0.25,0.25]
     print(value)
     print(zoomMe)
     camera.zoom=zoomMe
     print(camera.exposure_mode)
     return b'Setting Exposure Value'
    
    def quitStream(self):
        camera.close()
        pygame.quit()
        os.putenv('DISPLAY',':0.0')
        os.putenv('SDL_VIDEODRV','')
        os.putenv('SDL_FBDEV', '')
        sys.exit()
   
#resolution='3280x2464', 
try:
 if sys.argv[1]=="HighRes":
    CaptureRes="4056x3040"
 else:
    CaptureRes="640x480"
except:
    CaptureRes="640x480"
print("Capture Resolution: " + CaptureRes)
pygame.init()
#pitft = pigame.PiTft()
lcd = pygame.display.set_mode((320, 240))
lcd.fill((0,0,0))
pygame.display.update()
pygame.mouse.set_visible(False)
WHITE = (255,255,255)
screenfont = pygame.font.Font(None, 50)
headerfont=pygame.font.Font(None,20)

print("Starting Camera")
with picamera.PiCamera(resolution=CaptureRes, framerate=24) as camera:
    
    print("Create Stream")
    output = StreamingOutput()
    serveDir=os.path.dirname(os.path.abspath(__file__))
    
    print("Current Directory" + serveDir)
    camera.start_recording(output, format='mjpeg',splitter_port=2,resize=(320,240))
    
    #camera.wait_recording(1)
    #camera.shutter_speed = 6000000
    #camera.iso =100
    IP=check_output(['hostname', '-I']).decode('utf-8').split(" ")[0]   
    try:
        print("Start Camera App")
        myCamera=AstroPhotography()
        print("Start Streaming")
        while True:
         output.screen(myCamera,lcd)
         if button1.is_pressed:
            text_surface = screenfont.render('Taking Photo', True, WHITE)
            rect = text_surface.get_rect(center=(160,120))
            lcd.blit(text_surface, rect)
            pygame.display.update()
            
            myCamera.TakePhoto('false',5)
         elif button2.is_pressed:
            text_surface = screenfont.render(myCamera.cameraActions.nextValue(), True, WHITE)
            rect = text_surface.get_rect(center=(160,120))
            lcd.blit(text_surface, rect)
            pygame.display.update()
            sleep(2)
         elif button3.is_pressed:
             thisActionName=myCamera.cameraActions.currentValue()
             thisActionValue=getattr(myCamera,thisActionName + "Values").nextValue()
             thisAction=getattr(myCamera,thisActionName)(thisActionValue)
             sleep(2)
         elif button4.is_pressed:
             myCamera.quitStream() 
        
        
    #except KeyboardInterrupt:
    except: 
        print(sys.exec_info()[0])
    finally:
        print("Finishing")
        camera.close()
        pygame.quit()
        os.putenv('DISPLAY',':0.0')
        os.putenv('SDL_VIDEODRV','')
        os.putenv('SDL_FBDEV', '')
        sys.exit()
        
