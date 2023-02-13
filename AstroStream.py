import io
import picamera
import logging
from threading import Condition

import os, sys
from time import sleep
import time
from fractions import Fraction
from subprocess import check_output
#from PIL import Image
import INA219 as piHat
import pygame
#pigame
from pygame.locals import *
from gpiozero import Button


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
   def __init__(self,screen):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

        
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
   

class AstroPhotography(object):

    def __init__(self,camera,screen,stream):
        self.cameraActions=optionList(["SetISO","SetBrightness","SetZoom","SetCapture"],0)
        self.SetISOValues=optionList(["100","200","400","800"],0)
        self.SetBrightnessValues=optionList(["50","60","70","80","90"],0)
        self.SetZoomValues=optionList(["0","2","4"],0)
        self.SetCaptureValues=optionList(["Photo","Video","DarkFrame","Camera"],0)
        self.camera=camera
        self.screen=screen
        self.screenon=True
        self.WHITE = (255,255,255)
        self.screenfont = pygame.font.Font(None, 50)
        self.headerfont=pygame.font.Font(None,20)
        self.battery=piHat.INA219(addr=0x43)
        self.screen=screen
        self.stream=stream

    def screen(self,thisMessage):
        #with self.screenon:
            with self.stream.condition:
                         self.stream.condition.wait()
                         frame = self.stream.frame
             
            text_surface = self.headerfont.render(self.cameraActions.currentValue() + ": " + getattr(self,self.cameraActions.currentValue() + "Values").currentValue(), True, self.WHITE)
            text_surface2 = self.headerfont.render("IP: " + check_output(['hostname', '-I']  ).decode('utf-8').split(" ")[0] + "   Battery: {:3.1f}%".format((self.battery.getBusVoltage_V()-3)/1.2*100),True,self.WHITE)
            rect = text_surface.get_rect(center=(50,10))
            
            if thisMessage!="":
             msg_text_surface = self.screenfont.render(thisMessage, True, self.WHITE)
             msg_rect = text_surface.get_rect(center=(160,120)) 
            try:
             thisframe=pygame.image.load(io.BytesIO(frame),'JPEG')
             if self.SetCaptureValues.currentValue()=="Camera":
              thisframe=pygame.transform.flip(thisframe,True,True)
             #thisframe=pygame.image.frombuffer(io.BytesIO(frame))
            except pygame.error:
             logging.warning(pygame.get_error())
            self.screen.blit(thisframe,(0,0))
            self.screen.blit(text_surface, (5,5))
            self.screen.blit(text_surface2, (5,225))
            if thisMessage!="":  
               self.screen.blit(msg_text_surface, msg_rect)   
            try:
             pygame.display.update()
            except pygame.error:
             logging.warning(pygame.get_error())
            #pitft.update()   

    def TakePhoto(self,captureType,frames):
     rootDir=os.path.join(os.path.dirname(os.path.abspath(__file__)),'Images/Images')
     t = time.localtime()
     datestamp = time.strftime('%b-%d-%Y', t)
     timestamp = time.strftime('%b-%d-%Y_%H:%M:%S', t)
     os.makedirs(rootDir + datestamp, exist_ok=True)
                
     if captureType=="DarkFrame":
         fileName="DarkFrame"
     elif captureType=="Camera":
         fileName="Photo"
     else:
         fileName="AstroShot"
     totalFrames=int(frames)    
     #camera.framerate = Fraction(1, 6)
     #camera.shutter_speed = 6000000
     #camera.exposure_mode = 'off'
     #camera.iso=100
     logging.info('Called TakePhoto')
     for i in range(1,totalFrames+1,1):
      sleep(5)
      logging.info("Taking Photo %s of %s",str(i),str(totalFrames))
      if totalFrames>1:
         self.camera.capture(rootDir + datestamp + '/' + fileName + timestamp + 'Frame' + str(i) + '.jpg')
         sleep(10)
      else:
         self.camera.capture(rootDir + datestamp + '/' + fileName + timestamp + '.jpg')
           
     return b'Capturing photo'
    
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
     try:
      #self.camera.start_recording(rootDir + datestamp + '/AstroShot' + timestamp +'.h264',format='h264',resize=(1640,1232),splitter_port=1)
      self.camera.start_recording(rootDir + datestamp + '/AstroShot' + timestamp +'.h264',format='h264',splitter_port=1)   
      logging.info('Video Recording in progress')
      self.camera.wait_recording(60,splitter_port=1)
      self.camera.stop_recording(splitter_port=1)
      logging.info('Video Recording finished')
     except self.camera.exc.PiCameraError as e:
      logging.warning(str(e))
     return b'Capturing video'
     
    
    def SetISO(self,value):
     self.camera.iso=int(value)
     logging.info('Setting ISO %s' , self.camera.iso)
     return b'Setting ISO Value'
    
    def SetBrightness(self,value):
     self.camera.brightness=int(value)
     logging.info('Setting Brightness %s' , self.camera.brightness)
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
     
     self.camera.zoom=zoomMe
     
     return b'Setting Zoom'
    
    def quitStream(self,shutdown):
        self.camera.close()
        pygame.quit()
        if shutdown:
            os.system("sudo shutdown -h now") ; sys.exit(0)
        else:
            sys.exit()


button1 = Button(17)
button2 = Button(22)
button3 = Button(23)
button4 = Button(27)



def main():
 os.putenv('SDL_VIDEODRV','fbcon')
 os.putenv('SDL_FBDEV', '/dev/fb1')
 #os.putenv('SDL_MOUSEDRV','dummy')
 #os.putenv('SDL_MOUSEDEV','/dev/null')
 os.putenv('DISPLAY','')
 #resolution='3280x2464', 
 try:
  if sys.argv[1]=="HighRes":
     #CaptureRes="4056x3040"
      CaptureRes="1640x1232"
  else:
     CaptureRes="640x480"
 except:
    CaptureRes="640x480"

 os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)),'Images'),exist_ok=True)
 os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)),'logs'),exist_ok=True)
 logTimestamp = time.strftime('%b-%d-%Y', time.localtime())    
 logging.basicConfig(filename=os.path.dirname(os.path.abspath(__file__)) + '/logs/AstroPyPi.' + logTimestamp + '.log', level=logging.INFO,format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')    
 logging.info("Capture Resolution: %s" , CaptureRes)
 pygame.init()
 #pitft = pigame.PiTft()
 lcd = pygame.display.set_mode((320, 240))
 lcd.fill((0,0,0))
 pygame.display.update()
 pygame.mouse.set_visible(False)



 logging.info("Starting Camera")
 with picamera.PiCamera(resolution=CaptureRes, framerate=24) as camera:
    
    logging.info("Create Stream")
    streamOutput = StreamingOutput()
    serveDir=os.path.dirname(os.path.abspath(__file__))
    
    logging.info("Current Directory %s" , serveDir)
    camera.start_recording(streamOutput, format='mjpeg',splitter_port=2,resize=(320,240))
    
    
    IP=check_output(['hostname', '-I']).decode('utf-8').split(" ")[0]   
    try:
        logging.info("Start Camera App")
        myCamera=AstroPhotography(camera,lcd,streamOutput)
        logging.info("Start Streaming")
        #myCamera.TakePhoto('false',1)
        time.sleep(2)
        while True:
         myCamera.screen(myCamera,"")
         if button1.is_pressed:
            logging.info("Start Capture")
            #logging.info("Start Capture")
            output.screen(myCamera,lcd,'Taking ' + myCamera.SetCaptureValues.currentValue())
            #text_surface = output.screenfont.render('Taking ' + myCamera.SetCaptureValues.currentValue(), True, output.WHITE)
            #rect = text_surface.get_rect(center=(160,120))
            #lcd.blit(text_surface, rect)
            #pygame.display.update()
            logging.info("Checking Capture Mode")
            if myCamera.SetCaptureValues.currentValue()=="Photo":
             logging.info("Taking Photos")
             myCamera.TakePhoto(myCamera.SetCaptureValues.currentValue(),10)
            elif myCamera.SetCaptureValues.currentValue()=="Video":
             logging.info("Taking video")
             myCamera.captureVideo()
            elif myCamera.SetCaptureValues.currentValue()=="DarkFrame":
             logging.info("Taking dark frame")
             myCamera.TakePhoto(myCamera.SetCaptureValues.currentValue(),1)
            elif myCamera.SetCaptureValues.currentValue()=="Camera":
             logging.info("Taking Photo")
             myCamera.TakePhoto(myCamera.SetCaptureValues.currentValue(),1)
             
         elif button2.is_pressed:
            myCamera.screen(myCamera,lcd,myCamera.cameraActions.nextValue())
            #text_surface = output.screenfont.render(myCamera.cameraActions.nextValue(), True, output.WHITE)
            #rect = text_surface.get_rect(center=(160,120))
            #lcd.blit(text_surface, rect)
            #pygame.display.update()
            sleep(2)
         elif button3.is_pressed:
             thisActionName=myCamera.cameraActions.currentValue()
             thisActionValue=getattr(myCamera,thisActionName + "Values").nextValue()
             if thisActionName!="SetCapture":
              thisAction=getattr(myCamera,thisActionName)(thisActionValue)
              sleep(2)
         elif button4.is_pressed:
             
                text_quit = output.headerfont.render("Quit",True,output.WHITE)
                text_shutdown = output.headerfont.render("Shutdown",True,output.WHITE)
                text_back = output.headerfont.render("Back",True,output.WHITE)
                lcd.blit(text_quit, (280,50))
                lcd.blit(text_shutdown, (245,100))
                lcd.blit(text_back,(280,150))
                pygame.display.update()
                while True:
                 if button1.is_pressed:
                  myCamera.quitStream(False)
                 elif button2.is_pressed:
                  myCamera.quitStream(True)
                 elif button3.is_pressed:
                  break
        
    except KeyboardInterrupt:
    #except: 
       print(sys.exec_info()[0])
       logging.warning(sys.exec_info()[0])
    finally:
        logging.info("Finishing")
        camera.close()
        pygame.quit()
        sys.exit()
        

if __name__ == "__main__":
    main()
