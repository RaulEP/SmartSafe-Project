from subprocess import call
from flask import Flask, request ,redirect, send_from_directory, send_file
import requests
import RPi.GPIO as GPIO
import time

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

#LedEstadoPrograma
GPIO.setup(17, GPIO.OUT)
#LedEstadoCaptura
GPIO.setup(18, GPIO.OUT)
#Lock
GPIO.setup(22, GPIO.OUT)
#Flash
GPIO.setup(27, GPIO.OUT)

app = Flask(__name__)
GPIO.output(17, True)
GPIO.output(22, True)
GPIO.output(18, False)
GPIO.output(27, False)

@app.route('/rest/api/safe/Capture', methods=['GET'])
def Capture():
    r = CaptureImage()
    if r == False:
        return False
    else:
        ImagePath = r
        r = send_file(ImagePath)
        return r



@app.route('/rest/api/safe/Open', methods=['GET'])
def OpenSafe():
    GPIO.output(22, False)
    time.sleep(10)
    CloseSafe()

@app.route('/rest/api/safe/Close', methods=['GET'])
def CloseSafe():
    GPIO.output(22, True)

def CaptureImage():
    PicHome="/home/pi/WsSmartSafe/Image.jpg"
    GPIO.output(27, True)
    #sustituir este codigo con una llamada mas inteligente
    if call(["fswebcam", "-d","/dev/video0", "-D", "3" "-r", "1920x1080", str(PicHome)]) == 0:
        print("LLegue Hasta Aqui")
        #GPIO.output(17, False)
        BlinkRedLed()
        time.sleep(0.5)
        GPIO.output(27, False)
        time.sleep(0.5)
        GPIO.output(18, True)

        return str(PicHome)
    else:
        return False


def BlinkRedLed():
    c = 0 contador
    while c < 5: # Run forever
        GPIO.output(17, True) # Turn on
        sleep(0.5) # Sleep for 1 second
        GPIO.output(17, False) # Turn off
        sleep(0.5)
        c += 1





app.run(host='0.0.0.0', port=5001)
