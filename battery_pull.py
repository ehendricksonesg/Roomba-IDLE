"""
This script is used to constantly pull the Roomba's current battery capacity.
"""
try:  # Python 3  # create2api library is not compatible in it's current form
    from tkinter import ttk
    from tkinter import *  # causes tk widgets to be upgraded by ttk widgets
    import datetime

except ImportError:  # Python 2
    import sys, traceback  # trap exceptions
    import os  # switch off auto key repeat
    import Tkinter
    import ttk
    from Tkinter import *  # causes tk widgets to be upgraded by ttk widgets
    import tkFont as font  # button font sizing
    import json  # Create2API JSON file
    import create2api  # change serial port to '/dev/ttyAMA0'
    import datetime  # time comparison for Create2 sleep prevention routine
    import time  # sleep function
    import threading  # used to timeout Create2 function calls if iRobot has gone to sleep
    import math  # direction indicator (polygon) rotation
    import RPi.GPIO as GPIO  # BRC pin pulse

bot = create2api.Create2()


def bigbatts():
    print("yes " + str(bot.sensor_state['battery charge']) + " yes")
    time.sleep(1)


# create2api.sensor_data['battery capacity']
# str(bot.sensor_state['battery charge'])
