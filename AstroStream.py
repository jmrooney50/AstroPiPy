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
from PIL import Image
#Test with video stream capture

PAGE="""\
<html>
<head>
<title>picamera Astrophotography</title>
</head>
<body>
<script>
function AstroAction(ActionType) {
var url="/"
console.log(ActionType)

if(ActionType=="LightFrame")
{
url='/capture?&darkframe=False&frames=1';
}
else if(ActionType=="DarkFrame")
{
url='/capture?&darkframe=True&frames=1';
}
else if(ActionType=="MultiFrame")
{
url='/capture?&darkframe=False&frames=10';
}
else if (ActionType=="Video")
{
url='/captureVideo';
}
else if (ActionType=="Exposure")
{
url='/SetExposure?value=' + document.getElementById("ExposureMode").value;
}
else if (ActionType=="ISO")
{
url='/SetISO?value=' + document.getElementById("iso").value;
}
else if (ActionType=="Zoom")
{
url='/SetZoom?value=' + document.getElementById("zoom").value;
}

if(url!="/"){
console.log(url)
const Http = new XMLHttpRequest();
document.getElementById("TakePhoto").disabled=true
document.getElementById("TakeDarkFrame").disabled=true
document.getElementById("TakeVideo").disabled=true
document.getElementById("ExposureMode").disabled=true
document.getElementById("iso").disabled=true
document.getElementById("zoom").disabled=true
document.getElementById("TakeMultiFrame").disabled=true

Http.open("GET", url);
Http.send();

Http.onreadystatechange = (e) => {
  console.log(Http.responseText)
  document.getElementById("TakePhoto").disabled=false
  document.getElementById("TakeDarkFrame").disabled=false
document.getElementById("TakeVideo").disabled=false
document.getElementById("ExposureMode").disabled=false
document.getElementById("iso").disabled=false
document.getElementById("zoom").disabled=false
document.getElementById("TakeMultiFrame").disabled=false
}

}

}



</script>
<h1>Astrophotography</h1>
<div><table><tr><td>
<div width="80%">
<img src="stream" width="100%" />
</td><td>
<div width="20%">

<h1>Buttons</h1>
 
<button id="TakePhoto" type="submit" value="LightFrame" onclick="AstroAction(value)">Take Photo</button><br>
<button id="TakeMultiFrame" type="submit" value="MultiFrame" onclick="AstroAction(value)">Take Multiple Photos</button><br>
<button id="TakeDarkFrame" type="submit" value="DarkFrame" onclick="AstroAction(value)">Dark Frame</button><br>
<button id="TakeVideo" type="submit" value="Video" onclick="AstroAction(value)">Take Video</button><br>
<select name="Set ISO" id="iso" value="ISO" onchange="AstroAction('ISO')">
<option value="0">0</option>
<option value="100">100</option>
<option value="200">200</option>
<option value="400">400</option>
<option value="800">800</option>
</select><br><br>
<select name="ExposureMode" id="ExposureMode" value="Exposure" onchange="AstroAction('Exposure')">
<option value='off'>Off</option>
<option value='auto'>Auto</option>
<option value='night'>Night</option>
<option value="nightpreview">Night Preview</option>
<option value="backlight">Back Light</option>
<option value="spotlight">Spotlight</option>
<option value="sports">Sports</option>
<option value="snow">Snow</option>
<option value="beach">Beach</option>
<option value="verylong">Very Long</option>
<option value="fixedfps">Fixed FPS</option>
spl<option value="antishake">Antishake</option>
<option value="fireworks">Fireworks</option>
</select><br>
<select name="Set Zoom" id="zoom" value="zoom" onchange="AstroAction('Zoom')">
<option value="0">x1</option>
<option value="2">x2</option>
<option value="4">x4</option>
</select><br><br>
<a href="/images.html">Image Files</a>
</div></td></tr></table>
is</div>
</body>
</html>
"""
#class AstroStreaming(object):
 #   @cherr.expose
  #  def index(self):
   #  return PAGE
    
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
     return PAGE
    
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
