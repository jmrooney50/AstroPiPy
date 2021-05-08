import io
import picamera
import logging
import socketserver
from threading import Condition
from http import server
import webbrowser, os, sys
from time import sleep
import time
from fractions import Fraction
import cherrypy
from subprocess import check_output
#from PIL import Image
#Test with video stream capture


    
class StreamingOutput(object):
   def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        #self.buffer=picamera.PiCameraCircularIO(camera, seconds=5)
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

class AstroStreaming(object):
    @cherrypy.expose
    def index(self):
     return open('index.html')    
    @cherrypy.expose
    def stream(self):
            cherrypy.response.headers['Content-Type'] ='multipart/x-mixed-replace; boundary=FRAME'
    
            return self.content()
    stream._cp_config = {'response.stream': True}     

    def content(self):
             
             while True:
                    with output.condition:
                         output.condition.wait()
                         frame = output.frame
                                      
                    #frameBuf=io.BytesIO()
                    #imageFrame=Image.open(frame)
                    #imageFrame=imageFrame.resize((640,480))
                    #imageFrame.save(frameBuf,format='JPEG')
                    #frame=frameBuf.getvalue()
                    yield  b'--FRAME\r\nContent-Type:image/jpeg\r\nContent-Length:%d\r\n\r\n' % len(frame) + frame + b'\r\n'
    @cherrypy.expose
    def capture(self,darkframe,frames):
     rootDir=os.path.join(os.path.dirname(os.path.abspath(__file__)),'Images')
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
     for i in range(1,totalFrames+1,1):
      sleep(5)
      if totalFrames>1:
         camera.capture(rootDir + datestamp + '/' + fileName + timestamp + 'Frame' + str(i) + '.jpg')
      else:
         camera.capture(rootDir + datestamp + '/' + fileName + timestamp + '.jpg')
      sleep(10)
     #camera.exposure_mode = 'auto'
     return b'Capturing photo'
    
    @cherrypy.expose
    def captureVideo(self):
     rootDir=os.path.join(os.path.dirname(os.path.abspath(__file__)),'Images')
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
    @cherrypy.expose
    def SetISO(self,value):
     camera.iso=int(value)
     print(camera.iso)
     return b'Setting ISO Value'

    @cherrypy.expose
    def SetBrightness(self,value):
     camera.brightness=int(value)
     print(camera.brightness)
     return b'Setting ISO Value'
    
    @cherrypy.expose
    def SetExposure(self,value):
     camera.exposure_mode=value
     print(camera.exposure_mode)
     return b'Setting Exposure Value'
    @cherrypy.expose
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
#class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
 #   allow_reuse_address = True
  #  daemon_threads = True
def startupBrowser(chrome_path):
    webbrowser.get(chrome_path).open("http://localhost:8080")
#resolution='3280x2464', 
try:
 if sys.argv[1]=="HighRes":
    CaptureRes="4056x3040"
 else:
    CaptureRes="640x480"
except:
    CaptureRes="640x480"

with picamera.PiCamera(resolution=CaptureRes, framerate=24) as camera:
    recordingOutput=io.BytesIO()
    output = StreamingOutput()
    serveDir=os.path.dirname(os.path.abspath(__file__))
    
    print("Current Directory" + serveDir)
    #output = picamera.PiCameraCircularIO(camera, seconds=20)
    #camera.start_recording(recordingOutput, format='mjpeg')
    camera.start_recording(output, format='mjpeg',splitter_port=2,resize=(320,240))
    #camera.wait_recording(1)
    #camera.shutter_speed = 6000000
    #camera.iso =100
    IP=check_output(['hostname', '-I']).decode('utf-8').split(" ")[0]   
    try:
        #address = ('', 8080)
        #server = StreamingServer(address, StreamingHandler)
        cherrypy.config.update({'server.socket_host':IP})
        cherrypy.config.update({'/images': {'tools.staticdir.on':True,
                                'tools.staticdir.dir':os.path.join(serveDir,'Images')}})
         #                       #'tools.staticdir.index':'images.html'}})        
        #conf={'server.socket_host':IP,
              #                  '/images': {'tools.staticdir.on':True,
                   #             'tools.staticdir.dir':os.path.join(serveDir,'Images'),
                     #           'tools.staticdir.index':'images.html'}}
        cherrypy.quickstart(AstroStreaming())
        
        server.serve_forever()
        
    finally:
        camera.stop_recording()
