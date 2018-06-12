#!/usr/bin/python

import RPi.GPIO as GPIO # BRC pin pulse
import time             # sleep function

GPIO.setmode(GPIO.BCM)       # as opposed to GPIO.BOARD # Uses 'import RPi.GPIO as GPIO'
GPIO.setup(17, GPIO.OUT)     # pin 17 drives high to switch on BC337 transistor and CLEAN button 'ON'

GPIO.output(17, GPIO.HIGH)   # simulate CLEAN button press
time.sleep(.2)
GPIO.output(17, GPIO.LOW)
time.sleep(2)
 
GPIO.output(17, GPIO.HIGH)   # simulate CLEAN button press
time.sleep(.2)
GPIO.output(17, GPIO.LOW)
time.sleep(2)

GPIO.output(17, GPIO.HIGH)   # simulate CLEAN button press
time.sleep(.2)
GPIO.output(17, GPIO.LOW)
time.sleep(2)

GPIO.output(17, GPIO.HIGH)   # simulate CLEAN button press
time.sleep(.2)
GPIO.output(17, GPIO.LOW)
time.sleep(2)

GPIO.cleanup()
