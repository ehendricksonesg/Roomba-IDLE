#!/usr/bin/python

"""
iRobot Create 2 Dashboard
Nov 2016

Neil Littler
Python 2

Uses the well constructed Create2API library for controlling the iRobot through a single 'Create2' class.
Implemented OI codes:
- Start (enters Passive mode)
- Reset (enters Off mode)
- Stop  (enters Off mode.  Use when terminating connection)
- Baud
- Safe
- Full
- Clean
- Max
- Spot
- Seek Dock
- Power (down) (enters Passive mode. This a cleaning command)
- Set Day/Time
- Drive
- Motors PWM
- Digit LED ASCII
- Sensors

Added Create2API function:
    def buttons(self, button_number):
        # Push a Roomba button
        # 1=Clean 2=Spot 4=Dock 8=Minute 16=Hour 32=Day 64=Schedule 128=Clock
        
        noError = True

        if noError:
           self.SCI.send(self.config.data['opcodes']['buttons'], tuple([button_number]))
        else:
            raise ROIFailedToSendError("Invalid data, failed to send")



The iRobot Create 2 has 4 interface modes:
- Off      : When first switched on (Clean/Power button). Listens at default baud (115200 8N1). Battery charges.
- Passive  : Sleeps (power save mode) after 5 mins (1 min on charger) of inactivity and stops serial comms.
             Battery charges. Auto mode. Button input. Read only sensors information.
- Safe     : Never sleeps. Battery does not charge. Full control.
             If a safety condition occurs the iRobot reverts automatically to Passive mode.
- Full     : Never sleeps. Battery does not charge. Full control.
             Turns off cliff, wheel-drop and internal charger safety features.

iRobot Create 2 Notes:
- A Start() command or any clean command the OI will enter into Passive mode.
- In Safe or Full mode the battery will not charge nor will iRobot sleep after 5 mins,
  so you should issue a Passive() or Stop () command when you finish using the iRobot.
- A Stop() command will stop serial communication and the OI will enter into Off mode.
- A Power() command will stop serial communication and the OI will enter into Passive mode.
- Sensors can be read in Passive mode.
- The following conditions trigger a timer start that sleeps iRobot after 5 mins (or 1 min on charger):
  + single press of Clean/Power button (enters Passive mode)
  + Start() command not followed by Safe() or Full() commands
  + Reset() command
- When the iRobot is off and receives a (1 sec) low pulse of the BRC pin the OI (awakes and) listens at the default baud rate for a Start() command
- Command a 'Dock' button press (while docked) every 30 secs to prevent iRobot sleep
- Pulse BRC pin LOW every 30 secs to prevent Create2 sleep when undocked
- iRobot beeps once to acknowledge it is starting from Off mode when undocked

Tkinter reference:
- ttk widget classes are Button Checkbutton Combobox Entry Frame Label LabelFrame Menubutton Notebook 
         PanedWindow Progressbar Radiobutton Scale Scrollbar Separator Sizegrip Treeview
- I found sebsauvage.net/python/gui/# a good resource for coding good practices


"""
#import logging             # Activates the logging feature of Auklet
#logging.basicConfig(level=logging.DEBUG,
#                    format='(%(threadName)-10s) %(message)s')


try:                        # Python 3  # create2api library is not compatible in it's current form
    from tkinter import ttk
    from tkinter import *   # causes tk widgets to be upgraded by ttk widgets
    import datetime
    
except ImportError:         # Python 2
    import sys, traceback   # trap exceptions
    import os               # switch off auto key repeat
    import Tkinter
    import ttk
    from Tkinter import *   # causes tk widgets to be upgraded by ttk widgets
    import tkFont as font   # button font sizing
    import json             # Create2API JSON file
    import create2api       # change serial port to '/dev/ttyAMA0'
    import datetime         # time comparison for Create2 sleep prevention routine
    import time             # sleep function
    import threading        # used to timeout Create2 function calls if iRobot has gone to sleep
    import math             # direction indicator (polygon) rotation
    import RPi.GPIO as GPIO # BRC pin pulse
    import csv
    from auklet.monitoring import Monitoring


class Dashboard():

    def __init__(self, master):
        self.master = master
        self.InitialiseVars()
        self.paintGUI()
        self.master.bind('<Key>', self.on_keypress)        
        self.master.bind('<Left>', self.on_leftkey)        
        self.master.bind('<Right>', self.on_rightkey)        
        self.master.bind('<Up>', self.on_upkey)        
        self.master.bind('<Down>', self.on_downkey)
        self.master.bind('<KeyRelease>', self.on_keyrelease)
        os.system('xset -r off')  # turn off auto repeat key
        
    def on_press_driveforward(self, event):
        # print "Forward"
        self.driveforward = True

    def on_press_drivebackward(self, event):
        # print "Backward"
        self.drivebackward = True

    def on_press_driveleft(self, event):
        # print "Left"
        self.driveleft = True

    def on_press_driveright(self, event):
        # print "Right"
        self.driveright = True

    def on_press_stop(self, event):
        # print "Stop"
        self.driveforward = False
        self.drivebackward = False
        self.driveleft = False
        self.driveright = False

    def on_keypress(self, event):
        print("Key pressed "), repr(event.char)

    def on_leftkey(self, event):
        # print "Left"
        self.driveleft = True

    def on_rightkey(self, event):
        # print "Right"
        self.driveright = True

    def on_upkey(self, event):
        # print "Forward"
        self.driveforward = True
        
    def on_downkey(self, event):
        # print "Backward"
        self.drivebackward = True

    def on_keyrelease(self, event):
        # print "Stop"
        self.driveforward = False
        self.drivebackward = False
        self.driveleft = False
        self.driveright = False

    def on_leftbuttonclick(self, event):
        # origin for bearing mouse move
        global origin
        origin = event.x, event.y + 10        
        # calculate angle at bearing start point
        global bearingstart
        bearingstart = self.getangle(event)
        
        self.leftbuttonclick.set(True)
        self.xorigin = event.x
        self.yorigin = event.y
        self.commandvelocity = 0
        self.commandradius = 0
        #print str(event.x) + ":" + str(event.y)

    def on_leftbuttonrelease(self, event):
        self.leftbuttonclick.set(False)
        self.canvas.coords(self.bearing, 10, 30, 17.5, 5, 25, 30) 
        
    def on_motion(self, event):
        # calculate current bearing angle relative to initial angle
        global bearingstart
        angle = self.getangle(event) / bearingstart
        offset = complex(self.bearingcentre[0], self.bearingcentre[1])
        newxy = []
        for x, y in self.bearingxy:
            v = angle * (complex(x, y) - offset) + offset
            newxy.append(v.real)
            newxy.append(v.imag)
        self.canvas.coords(self.bearing, *newxy) 
        
        #print str(self.xorigin - event.x) + ":" + str(self.yorigin - event.y)
        if self.xorigin - event.x > 0:
            # turn left
            self.commandradius = (200 - (self.xorigin - event.x)) * 10
            if self.commandradius < 5: self.commandradius = 1
            if self.commandradius > 1950: self.commandradius = 32767
        else:
            # turn right
            self.commandradius = ((event.x - self.xorigin) - 200) * 10
            if self.commandradius > -5: self.commandradius = -1
            if self.commandradius < -1950: self.commandradius = 32767

        if self.yorigin - event.y > 0:
            # drive forward
            self.commandvelocity = self.yorigin - event.y
            if self.commandvelocity > 150: self.commandvelocity = 150
            self.commandvelocity = (int(self.speed.get()) * self.commandvelocity) / 150
        else:
            # drive backward
            self.commandvelocity = -1 * (event.y - self.yorigin)
            if self.commandvelocity < -150: self.commandvelocity = -150
            self.commandvelocity = (int(self.speed.get()) * self.commandvelocity) / 150
            
        #print 'iRobot velocity, radius is ' + str(self.commandvelocity) + "," + str(self.commandradius)           

    def getangle(self, event):
        dx = event.x - origin[0]
        dy = event.y - origin[1]
        try:
            return complex(dx, dy) / abs(complex(dx, dy))
        except ZeroDivisionError:
            return 0.0 # cannot determine angle 

    def on_press_chgdrive(self):
        if self.driven.get() == 'Button\ndriven':
            self.driven.set('Mouse\ndriven')
            self.btnForward.configure(state=DISABLED)            
            self.btnBackward.configure(state=DISABLED)
            self.btnLeft.configure(state=DISABLED)
            self.btnRight.configure(state=DISABLED)
        else:
            self.driven.set('Button\ndriven')
            self.btnForward.configure(state=NORMAL)            
            self.btnBackward.configure(state=NORMAL)
            self.btnLeft.configure(state=NORMAL)
            self.btnRight.configure(state=NORMAL)
        
    def on_exit(self):
        # Uses 'import tkMessageBox as messagebox' for Python2 or 'import tkMessageBox' for Python3 and 'root.protocol("WM_DELETE_WINDOW", on_exit)'
        #if messagebox.askokcancel("Quit", "Do you want to quit?"):
        # print "Exiting irobot-dashboard"
        os.system('set -r on') # turn on auto repeat key
        self.exitflag = True
        #GPIO.cleanup()
        #self.master.destroy()

    def on_select_datalinkconnect(self):
        if self.rbcomms.cget('selectcolor') == 'red':
            self.dataconn.set(True)
        elif self.rbcomms.cget('selectcolor') == 'lime green':
            self.dataretry.set(True)
        
    def on_mode_change(self, *args):
        self.ledsource.set('mode')
        self.modeflag.set(True)
        # print "OI mode change from " +  self.mode.get() + " to " + self.chgmode.get()
            
    def on_led_change(self, *args):
        self.ledsource.set('test')
            
    def InitialiseVars(self):
        # declare variable classes=StringVar, BooleanVar, DoubleVar, IntVar
        self.voltage = StringVar()   ; self.voltage.set('0')     # Battery voltage (mV)
        self.current = StringVar()   ; self.current.set('0')     # Battery current in or out (mA)
        self.capacity = StringVar()  ; self.capacity.set('0')    # Battery capacity (mAh)
        self.temp = StringVar()      ; self.temp.set('0')        # Battery temperature (Degrees C)

        self.dataconn = BooleanVar() ; self.dataconn.set(True)   # Attempt a data link connection with iRobot
        self.dataretry = BooleanVar(); self.dataretry.set(False) # Retry a data link connection with iRobot
        self.chgmode = StringVar()   ; self.chgmode.set('')      # Change OI mode
        self.chgmode.trace('w', self.on_mode_change)             # Run function when value changes
        self.modeflag = BooleanVar() ; self.modeflag.set(False)  # Request to change OI mode
        self.mode = StringVar()                                  # Current operating OI mode
        self.TxVal = StringVar()     ; self.TxVal.set('0')       # Num transmitted packets
        
        self.leftmotor = StringVar() ; self.leftmotor.set('0')   # Left motor current (mA)
        self.rightmotor = StringVar(); self.rightmotor.set('0')  # Left motor current (mA)

        self.speed = StringVar()                                 # Maximum drive speed     
        self.driveforward = BooleanVar()    ; self.driveforward.set(False)
        self.drivebackward = BooleanVar()   ; self.drivebackward.set(False)
        self.driveleft = BooleanVar()       ; self.driveleft.set(False)
        self.driveright = BooleanVar()      ; self.driveright.set(False)
        self.leftbuttonclick = BooleanVar() ; self.leftbuttonclick.set(False)
        self.commandvelocity = IntVar()     ; self.commandvelocity.set(0)
        self.commandradius = IntVar()       ; self.commandradius.set(0)
        self.driven = StringVar()           ; self.driven.set('Button\ndriven')
        self.xorigin = IntVar()             ; self.xorigin = 0   # mouse x coord
        self.yorigin = IntVar()             ; self.yorigin = 0   # mouse x coord

        self.velocity = StringVar()  ; self.velocity.set('0')    # Velocity requested (mm/s)
        self.radius = StringVar()    ; self.radius.set('0')      # Radius requested (mm)
        self.angle = StringVar()     ; self.angle.set('0')       # Angle in degrees turned since angle was last requested
        self.odometer = StringVar()  ; self.odometer.set('0')    # Distance traveled in mm since distance was last requested

        self.lightbump = StringVar()        ; self.lightbump.set('0')
        self.lightbumpleft = StringVar()    ; self.lightbumpleft.set('0')
        self.lightbumpfleft = StringVar()   ; self.lightbumpfleft.set('0')
        self.lightbumpcleft = StringVar()   ; self.lightbumpcleft.set('0')
        self.lightbumpcright = StringVar()  ; self.lightbumpcright.set('0')
        self.lightbumpfright = StringVar()  ; self.lightbumpfright.set('0')
        self.lightbumpright = StringVar()   ; self.lightbumpright.set('0')

        self.DSEG = StringVar()                                  # 7 segment display
        self.DSEG.trace('w', self.on_led_change)                 # Run function when value changes
        self.ledsource = StringVar() ; self.ledsource.set('mode')# Determines what data to display on DSEG

        self.exitflag = BooleanVar() ; self.exitflag = False     # Exit program flag

    def paintGUI(self):
        
        self.master.geometry('980x670+20+50')
        self.master.wm_title("iRobot Dashboard")
        self.master.configure(background='white')
        self.master.protocol("WM_DELETE_WINDOW", self.on_exit)

        s = ttk.Style()
        # theme=CLAM,ALT,CLASSIC,DEFAULT
        s.theme_use('clam')
        s.configure("orange.Horizontal.TProgressbar", foreground="orange", background='orange')
        s.configure("red.Horizontal.TProgressbar", foreground="red", background='red')
        s.configure("blue.Horizontal.TProgressbar", foreground="blue", background='blue')
        s.configure("green.Horizontal.TProgressbar", foreground="green", background='green')
        s.configure("limegreen.Vertical.TProgressbar", foreground="lime green", background='blue')


        # TOP LEFT FRAME - BATTERY
        # frame relief=FLAT,RAISED,SUNKEN,GROOVE,RIDGE
        frame = Frame(self.master, bd=1, width=330, height=130, background='white', relief=GROOVE)
        
        # labels
        Label(frame, text="BATTERY", background='white').pack()
        label = Label(frame, text="V", background='white')
        label.pack()
        label.place(x=230, y=32)
        self.lblCurrent = Label(frame, text="mA", background='white')
        self.lblCurrent.pack()
        self.lblCurrent.place(x=230, y=52)
        label = Label(frame, text="mAH Capacity", background='white')
        label.pack()
        label.place(x=230, y=72)
        label = Label(frame, text="Temp 'C", background='white')
        label.pack()
        label.place(x=230, y=92)

        # telemetry display
        label = Label(frame, textvariable=self.voltage, font=("DSEG7 Classic",16), anchor=E, background='white', width=4)
        label.pack()
        label.place(x=170, y=30)
        label = Label(frame, textvariable=self.current, font=("DSEG7 Classic",16), anchor=E, background='white', width=4)
        label.pack()
        label.place(x=170, y=50)
        label = Label(frame, textvariable=self.capacity, font=("DSEG7 Classic",16), anchor=E, background='white', width=4)
        label.pack()
        label.place(x=170, y=70)
        label = Label(frame, textvariable=self.temp, font=("DSEG7 Classic",16), anchor=E, background='white', width=4)
        label.pack()
        label.place(x=170, y=90)
        
        # progress bars
        pb = ttk.Progressbar(frame, variable=self.voltage, style="orange.Horizontal.TProgressbar", orient="horizontal", length=150, mode="determinate")
        pb["maximum"] = 20
        #pb["value"] = 15
        pb.pack()
        pb.place(x=10, y=31)
        self.pbCurrent = ttk.Progressbar(frame, variable=self.current, style="orange.Horizontal.TProgressbar", orient="horizontal", length=150, mode="determinate")
        self.pbCurrent["maximum"] = 1000
        #self.pbCurrent["value"] = 600
        self.pbCurrent.pack()
        self.pbCurrent.place(x=10, y=51)
        self.pbCapacity = ttk.Progressbar(frame, variable=self.capacity, style="orange.Horizontal.TProgressbar", orient="horizontal", length=150, mode="determinate")
        self.pbCapacity["maximum"] = 3000
        #self.pbCapacity["value"] = 2000
        self.pbCapacity.pack()
        self.pbCapacity.place(x=10, y=71)
        pb = ttk.Progressbar(frame, variable=self.temp, style="orange.Horizontal.TProgressbar", orient="horizontal", length=150, mode="determinate")
        pb["maximum"] = 50
        #pb["value"] = 40
        pb.pack()
        pb.place(x=10, y=91)

        #frame.pack()
        frame.pack_propagate(0) # prevents frame autofit
        frame.place(x=10, y=10)


        # MIDDLE LEFT FRAME - MOTORS
        frame = Frame(self.master, bd=1, width=330, height=130, background='white', relief=GROOVE)

        # labels
        Label(frame, text="MOTOR", background='white').pack()
        label = Label(frame, text="Left", background='white')
        label.pack()
        label.place(x=50, y=25)
        label = Label(frame, text="Right", background='white')
        label.pack()
        label.place(x=160, y=25)

        # telemetry display
        label = Label(frame, textvariable=self.leftmotor, font=("DSEG7 Classic",16), anchor=E, background='white', width=7)
        label.pack()
        label.place(x=10, y=70)
        label = Label(frame, textvariable=self.rightmotor, font=("DSEG7 Classic",16), anchor=E, background='white', width=7)
        label.pack()
        label.place(x=130, y=70)

        # progress bars
        pb = ttk.Progressbar(frame, variable=self.leftmotor, style="orange.Horizontal.TProgressbar", orient="horizontal", length=100, mode="determinate")
        pb["maximum"] = 300
        #pb["value"] = 60
        pb.pack()
        pb.place(x=10, y=45)

        pb = ttk.Progressbar(frame, variable=self.rightmotor, style="orange.Horizontal.TProgressbar", orient="horizontal", length=100, mode="determinate")
        pb["maximum"] = 300
        #pb["value"] = 60
        pb.pack()
        pb.place(x=130, y=45)
        
        label = Label(frame, text="mA", background='white')
        label.pack()
        label.place(x=230, y=72)

        #frame.pack()
        frame.pack_propagate(0) # prevents frame autofit
        frame.place(x=10, y=150)


        # TOP RIGHT FRAME - DATA LINK
        frame = Frame(self.master, bd=1, width=330, height=130, background='white', relief=GROOVE)

        # labels
        Label(frame, text="DATA LINK", background='white').pack()
        self.rbcomms = Radiobutton(frame, state=DISABLED, background='white', value=1, command=self.on_select_datalinkconnect, relief=FLAT, disabledforeground='white', selectcolor='red', borderwidth=0)
        self.rbcomms.pack()
        self.rbcomms.place(x=208, y=1)

        label = Label(frame, text="OI Mode", background='white')
        label.pack()
        label.place(x=10, y=35)
        label = Label(frame, text="Change OI Mode", background='white')
        label.pack()
        label.place(x=10, y=65)
        label = Label(frame, text="Num Packets Tx", background='white')
        label.pack()
        label.place(x=10, y=95)

        # telemetry display
        label = Label(frame, textvariable=self.mode, anchor=W, background='snow2', width=10)
        label.pack()
        label.place(x=150, y=34)
        label = Label(frame, textvariable=self.TxVal, state=NORMAL, font=("DSEG7 Classic",16), anchor=E, background='snow2', width=11)
        label.pack()
        label.place(x=150, y=94)

        # combobox
        self.cmbMode = ttk.Combobox(frame, values=('Passive', 'Safe', 'Full', 'Seek Dock'), textvariable=self.chgmode, width=10)
        #self.cmbMode['values'] = ('Passive', 'Safe', 'Full', 'Seek Dock')
        self.cmbMode.pack()
        self.cmbMode.place(x=150,y=63)      
        
        #frame.pack()
        frame.pack_propagate(0) # prevents frame autofit
        frame.place(x=640, y=10)


        # MIDDLE RIGHT FRAME - DRIVE
        frame = Frame(self.master, bd=1, width=330, height=130, background='white', relief=GROOVE)

        # labels
        Label(frame, text="DRIVE", background='white').pack()
        label = Label(frame, text="Speed (mm/s)", background='white')
        label.pack()
        label.place(x=10, y=10)

        # scale
        self.scale = Scale(frame, variable=self.speed, relief=GROOVE, orient=VERTICAL, from_=500, to=0, length=83, width=10)
        self.scale.pack()
        self.scale.place(x=25, y=30)
        self.scale.set(100)

        #pb = ttk.Progressbar(frame, style="blue.Vertical.TProgressbar", orient="vertical", length=70, mode="determinate")

        # buttons
        self.btnForward = ttk.Button(frame, text="^")
        self.btnForward.pack()
        self.btnForward.place(x=145, y=20)
        self.btnForward.bind("<ButtonPress>", self.on_press_driveforward)
        self.btnForward.bind("<ButtonRelease>", self.on_press_stop)

        self.btnBackward = ttk.Button(frame, text="v")
        self.btnBackward.pack()
        self.btnBackward.place(x=147, y=90)
        self.btnBackward.bind("<ButtonPress>", self.on_press_drivebackward)
        self.btnBackward.bind("<ButtonRelease>", self.on_press_stop)

        self.btnLeft = ttk.Button(frame, text="<")
        self.btnLeft.pack()
        self.btnLeft.place(x=87, y=55)
        self.btnLeft.bind("<ButtonPress>", self.on_press_driveleft)
        self.btnLeft.bind("<ButtonRelease>", self.on_press_stop)

        self.btnRight = ttk.Button(frame, text=">")
        self.btnRight.pack()
        self.btnRight.place(x=205, y=55)
        self.btnRight.bind("<ButtonPress>", self.on_press_driveright)
        self.btnRight.bind("<ButtonRelease>", self.on_press_stop)

        frame.bind('<Button-1>', self.on_leftbuttonclick)
        frame.bind('<ButtonRelease-1>', self.on_leftbuttonrelease)
        frame.bind('<B1-Motion>', self.on_motion)

        # Uses 'import tkinter.font as font' to facilitate button sizing for Python 3
        btnfont = font.Font(size=9)
        button = Button(frame, textvariable=self.driven, command=self.on_press_chgdrive)
        button['font'] = btnfont
        button.pack()
        button.place(x=253, y=20)

        #frame.pack()
        frame.pack_propagate(0) # prevents frame autofit
        frame.place(x=640, y=150)


        # BOTTOM FRAME - SENSORS
        frame = Frame(self.master, bd=1, width=960, height=280, background='white', relief=GROOVE)

        # labels
        Label(frame, text="SENSORS", background='white').pack()

        label = Label(frame, text="Telemetry", background='white', anchor=E)
        label.pack()
        label.place(x=50, y=25)
        label = Label(frame, text="Commanded Velocity (mm/s)", background='white', anchor=E)
        label.pack()
        label.place(x=10, y=55)
        label = Label(frame, text="Commanded Radius (mm)", background='white', anchor=E)
        label.pack()
        label.place(x=10, y=85)
        label = Label(frame, text="Angle (degrees)", background='white', anchor=E)
        label.pack()
        label.place(x=10, y=115)
        label = Label(frame, text="Odometer (mm)", background='white', anchor=E)
        label.pack()
        label.place(x=10, y=145)

        label = Label(frame, text="7 Segment Display", background='white', anchor=E)
        label.pack()
        label.place(x=10, y=198)

        label = Label(frame, text="Cliff Signal", background='white')
        label.pack()
        label.place(x=433, y=25)
        label = Label(frame, text="Cliff Left", background='white')
        label.pack()
        label.place(x=450, y=55)
        label = Label(frame, text="Cliff Front Left", background='white')
        label.pack()
        label.place(x=450, y=85)
        label = Label(frame, text="Cliff Front Right", background='white')
        label.pack()
        label.place(x=450, y=115)
        label = Label(frame, text="Cliff Right", background='white')
        label.pack()
        label.place(x=450, y=145)
        label = Label(frame, text="Wall", background='white')
        label.pack()
        label.place(x=450, y=175)
        label = Label(frame, text="Virtual Wall", background='white')
        label.pack()
        label.place(x=450, y=205)

        label = Label(frame, text="Light Bumper", background='white')
        label.pack()
        label.place(x=740, y=25)
        label = Label(frame, text="Bumper Detect (binary)", background='white')
        label.pack()
        label.place(x=770, y=55)
        label = Label(frame, text="Light Bump Left", background='white')
        label.pack()
        label.place(x=770, y=85)
        label = Label(frame, text="Light Bump Front Left", background='white')
        label.pack()
        label.place(x=770, y=115)
        label = Label(frame, text="Light Bump Centre Left", background='white')
        label.pack()
        label.place(x=770, y=145)
        label = Label(frame, text="Light Bump Centre Right", background='white')
        label.pack()
        label.place(x=770, y=175)
        label = Label(frame, text="Light Bump Front Right", background='white')
        label.pack()
        label.place(x=770, y=205)
        label = Label(frame, text="Light Bump Right", background='white')
        label.pack()
        label.place(x=770, y=235)
          
        # telemetry display
        label = Label(frame, textvariable=self.velocity, font=("DSEG7 Classic",16), anchor=E, background='snow2', width=8)
        label.pack()
        label.place(x=195, y=53)
        label = Label(frame, textvariable=self.radius, font=("DSEG7 Classic",16), anchor=E, background='snow2', width=8)
        label.pack()
        label.place(x=195, y=83)
        label = Label(frame, textvariable=self.angle, font=("DSEG7 Classic",16), anchor=E, background='snow2', width=8)
        label.pack()
        label.place(x=195, y=113)
        label = Label(frame, textvariable=self.odometer, font=("DSEG7 Classic",16), anchor=E, background='snow2', width=8)
        label.pack()
        label.place(x=195, y=143)

        label = Label(frame, textvariable=self.DSEG, text="8888", font=("DSEG7 Classic",45), anchor=E, background='snow2', width=4)
        label.pack()
        label.place(x=155, y=200)

        label = Label(frame, textvariable=self.lightbump, font=("DSEG7 Classic",16), anchor=E, background='snow2', width=6)
        label.pack()
        label.place(x=663, y=53)
        label = Label(frame, textvariable=self.lightbumpleft, font=("DSEG7 Classic",16), anchor=E, background='snow2', width=4)
        label.pack()
        label.place(x=690, y=83)
        label = Label(frame, textvariable=self.lightbumpfleft, font=("DSEG7 Classic",16), anchor=E, background='snow2', width=4)
        label.pack()
        label.place(x=690, y=113)
        label = Label(frame, textvariable=self.lightbumpcleft, font=("DSEG7 Classic",16), anchor=E, background='snow2', width=4)
        label.pack()
        label.place(x=690, y=143)
        label = Label(frame, textvariable=self.lightbumpcright, font=("DSEG7 Classic",16), anchor=E, background='snow2', width=4)
        label.pack()
        label.place(x=690, y=173)
        label = Label(frame, textvariable=self.lightbumpfright, font=("DSEG7 Classic",16), anchor=E, background='snow2', width=4)
        label.pack()
        label.place(x=690, y=203)
        label = Label(frame, textvariable=self.lightbumpright, font=("DSEG7 Classic",16), anchor=E, background='snow2', width=4)
        label.pack()
        label.place(x=690, y=233)

        # radio buttons
        self.rbcl = Radiobutton(frame, state= DISABLED, background='white', value=1, relief=FLAT, disabledforeground='white', foreground='orange', selectcolor='orange', borderwidth=0)
        self.rbcl.pack()
        self.rbcl.place(x=420, y=55)
        self.rbcfl = Radiobutton(frame, state= DISABLED, background='white', value=1, relief=FLAT, disabledforeground='white', foreground='orange', selectcolor='orange', borderwidth=0)
        self.rbcfl.pack()
        self.rbcfl.place(x=420, y=85)
        self.rbcfr = Radiobutton(frame, state= DISABLED, background='white', value=1, relief=FLAT, disabledforeground='white', foreground='orange', selectcolor='orange', borderwidth=0)
        self.rbcfr.pack()
        self.rbcfr.place(x=420, y=115)
        self.rbcr = Radiobutton(frame, state= DISABLED, background='white', value=1, relief=FLAT, disabledforeground='white', foreground='orange', selectcolor='orange', borderwidth=0)
        self.rbcr.pack()
        self.rbcr.place(x=420, y=145)
        self.rbw = Radiobutton(frame, state= DISABLED, background='white', value=1, relief=FLAT, disabledforeground='white', foreground='orange', selectcolor='orange', borderwidth=0)
        self.rbw.pack()
        self.rbw.place(x=420, y=175)
        self.rbvw = Radiobutton(frame, state= DISABLED, background='white', value=1, relief=FLAT, disabledforeground='white', foreground='orange', selectcolor='orange', borderwidth=0)
        self.rbvw.pack()
        self.rbvw.place(x=420, y=205)   

        # scale
        scale = Scale(frame, showvalue=8888, variable=self.DSEG, relief=GROOVE, orient=HORIZONTAL, from_=0, to=8888, length=125, width=10)
        scale.pack()
        scale.place(x=10, y=217)
        scale.set(8888)
        
        #frame.pack()
        frame.pack_propagate(0) # prevents frame autofit
        frame.place(x=10,y=290)


        # iRobot Create 2 image
        #image = Image.open('create2.gif')     uses 'from PIL import Image'
        #image = image.rotate(90)
        #image = image.resize((100,100))
        create2 = PhotoImage(file="create2.gif")
        img = Label(self.master, image=create2, background='white')
        img.photo = create2
        img.pack()
        img.place(x=415, y=80)

        # iRobot bearing indicator
        self.canvas = Canvas(width=35, height=35, background='white', borderwidth=0, state=NORMAL)
        self.canvas.pack()
        self.canvas.place(x=474, y=35)
        self.bearingcentre = (17.5, 18.5)
        self.bearingxy = [(10,30),(17.5,5),(25,30)]
        self.bearing = self.canvas.create_polygon(self.bearingxy, fill='black')
        #self.canvas.coords(self.bearing, (0,0,10,25,20,0)) # change direction
        

        # radio buttons
        self.rbul = Radiobutton(self.master, state= DISABLED, background='white', value=1, relief=FLAT, disabledforeground='white', foreground='orange', selectcolor='orange', borderwidth=0)
        self.rbul.pack()
        self.rbul.place(x=410, y=75)
        self.rbur = Radiobutton(self.master, state= DISABLED, background='white', value=1, relief=FLAT, disabledforeground='white', foreground='orange', selectcolor='orange', borderwidth=0)
        self.rbur.pack()
        self.rbur.place(x=549, y=75)
        self.rbdl = Radiobutton(self.master, state= DISABLED, background='white', value=1, relief=FLAT, disabledforeground='white', foreground='orange', selectcolor='orange', borderwidth=0)
        self.rbdl.pack()
        self.rbdl.place(x=453, y=144)
        self.rbdr = Radiobutton(self.master, state= DISABLED, background='white', value=1, relief=FLAT, disabledforeground='white', foreground='orange', selectcolor='orange', borderwidth=0)
        self.rbdr.pack()
        self.rbdr.place(x=506, y=144)

        # flash an initialisation
        self.master.update()
        self.master.after(200)
        self.rbul.configure(state=NORMAL)
        self.rbul.select()
        self.rbur.configure(state=NORMAL)
        self.rbur.select()
        self.rbdl.configure(state=NORMAL)
        self.rbdl.select()
        self.rbdr.configure(state=NORMAL)       
        self.rbdr.select()
        self.rbcl.configure(state=NORMAL)
        self.rbcl.select()
        self.rbcfl.configure(state=NORMAL)
        self.rbcfl.select()
        self.rbcr.configure(state=NORMAL)
        self.rbcr.select()
        self.rbcfr.configure(state=NORMAL)
        self.rbcfr.select()
        self.rbw.configure(state=NORMAL)
        self.rbw.select()
        self.rbvw.configure(state=NORMAL)
        self.rbvw.select()
        #TxVal.set("ABCDEFGHIJK")
       
        self.master.update()
        self.rbul.configure(state=DISABLED)
        self.rbur.configure(state=DISABLED)
        self.rbdl.configure(state=DISABLED)
        self.rbdr.configure(state=DISABLED)
        self.rbcl.configure(state=DISABLED)
        self.rbcfl.configure(state=DISABLED)
        self.rbcr.configure(state=DISABLED)
        self.rbcfr.configure(state=DISABLED)
        self.rbw.configure(state=DISABLED)
        self.rbvw.configure(state=DISABLED)

    def comms_check(self, flag):
        if flag == 1:     # have comms
            self.rbcomms.configure(state=NORMAL, selectcolor='lime green', foreground='lime green')
            self.rbcomms.select()
        elif flag == 0:   # no comms
            self.rbcomms.configure(state=NORMAL, selectcolor='red', foreground='red')
            self.rbcomms.select()
        elif flag == -1:  # for flashing radio button
            self.rbcomms.configure(state=DISABLED)


def timelimit(timeout, func, args=(), kwargs={}):
    """ Run func with the given timeout. If func didn't finish running
        within the timeout, raise TimeLimitExpired
    """
    class FuncThread(threading.Thread):
        def __init__(self):
            threading.Thread.__init__(self)
            self.result = None
            
        def run(self):
            self.result = func(*args, **kwargs)

    it = FuncThread()
    it.start()
    it.join(timeout)
    if it.isAlive():
        return False
    else:
        return True

       
def RetrieveCreateTelemetrySensors(dashboard):

    create_data = """
                  {"OFF" : 0,
                   "PASSIVE" : 1,
                   "SAFE" : 2,
                   "FULL" : 3,
                   "NOT CHARGING" : 0,
                   "RECONDITIONING" : 1,
                   "FULL CHARGING" : 2,
                   "TRICKLE CHARGING" : 3,
                   "WAITING" : 4,
                   "CHARGE FAULT" : 5
                   }
                   """
                   
    create_dict = json.loads(create_data)

    # a timer for issuing a button command to prevent Create2 from sleeping in Passive mode    
    BtnTimer = datetime.datetime.now() + datetime.timedelta(seconds=30)
    battcharging = False
    docked = False
    connection_attempt = 0
    
    global CLNpin, BRCpin
    CLNpin = 17                      # GPIO 17 to control CLEAN button
    BRCpin = 18                      # GPIO 18 to negative pulse BRC pin on miniDIN port
    GPIO.setmode(GPIO.BCM)           # as opposed to GPIO.BOARD # Uses 'import RPi.GPIO as GPIO'
    GPIO.setup(CLNpin, GPIO.OUT)     # GPIO pin 17 drives high to switch on BC337 transistor and CLEAN button 'ON'
    GPIO.setup(BRCpin, GPIO.OUT)     # GPIO pin 18 drives low on Create2 BRC pin
    GPIO.output(CLNpin, GPIO.LOW)    # initial state
    GPIO.output(BRCpin, GPIO.HIGH)   # initial state
    time.sleep(1)
    GPIO.output(BRCpin, GPIO.LOW)    # pulse BRC pin LOW to wake up irobot if in Off mode and listen at 115200 baud
    time.sleep(1)
    GPIO.output(BRCpin, GPIO.HIGH)   # rest state
    
    while True and not dashboard.exitflag: # outer loop to handle data link retry connect attempts
        
        if dashboard.dataconn.get() == True:

            # print "Attempting data link connection"
            dashboard.comms_check(-1)
            dashboard.master.update()
            
            bot = create2api.Create2()
            bot.digit_led_ascii('    ') # clear DSEG before Passive mode
            # print "Issuing a Start()"
            bot.start()                 # issue passive mode command
            #bot.safe()
            dist = 0                    # reset odometer
            connection_attempt += 1

            while True and not dashboard.exitflag:
                        
                try:
                    # check if serial is communicating
                    time.sleep(0.25)
                    if timelimit(1, bot.get_packet, (100, ), {}) == False:  # run bot.get_packet(100) with a timeout

                        # print "Data link down"
                        dashboard.comms_check(0)
                        bot.destroy()
                        if connection_attempt > 5:
                            connection_attempt = 0
                            # print "Attempted 6 communication connections... sleeping for 6 mins..."
                            time.sleep(360)
                        # print "Simulating a Clean button press"
                        GPIO.output(CLNpin, GPIO.HIGH) # Single press of Clean button enters Passive mode
                        time.sleep(.2)
                        GPIO.output(CLNpin, GPIO.LOW)  # Clean button activates on button 'release'
                        dashboard.dataconn.set(True)
                        break

                    else:
                        
                        # DATA LINK
                        connection_attempt = 0
                        if dashboard.dataconn.get() == True:
                            # print "Data link up"
                            dashboard.dataconn.set(False)

                        if dashboard.dataretry.get() == True:   # retry an unstable (green) connection
                            # print "Data link reconnect"
                            dashboard.dataretry.set(False)
                            dashboard.dataconn.set(True)
                            dashboard.comms_check(0)
                            bot.destroy()
                            break

                        if dashboard.rbcomms.cget('state') == "normal":  # flash radio button
                            dashboard.comms_check(-1)
                        else:
                            dashboard.comms_check(1)


                        # SLEEP PREVENTION
                        # set BRC pin HIGH
                        GPIO.output(BRCpin, GPIO.HIGH)
                        
                        # command a 'Dock' button press (while docked) every 30 secs to prevent Create2 sleep 
                        # pulse BRC pin LOW every 30 secs to prevent Create2 sleep when undocked
                        # (BRC pin pulse to prevent sleep not working for me)
                        if datetime.datetime.now() > BtnTimer:
                            GPIO.output(BRCpin, GPIO.LOW)
                            # print 'BRC pin pulse'
                            BtnTimer = datetime.datetime.now() + datetime.timedelta(seconds=30)
                            if docked:
                                # print 'Dock'
                                bot.buttons(4) # 1=Clean 2=Spot 4=Dock 8=Minute 16=Hour 32=Day 64=Schedule 128=Clock
                            # switch to safe mode if undocked and detects OI mode is Passive
                            # (no longer required with Clean button press simulation)
                            elif bot.sensor_state['oi mode'] == create_dict["PASSIVE"] and \
                                 dashboard.chgmode.get() != 'Seek Dock':
                                dashboard.chgmode.set('Safe') 
                                bot.safe()
                                
                        dashboard.TxVal.set(str(int(dashboard.TxVal.get()) + 80)) # add 80 packets to TxVal


                        # OI MODE     
                        if bot.sensor_state['oi mode'] == create_dict["PASSIVE"]:
                            dashboard.mode.set("Passive")
                        elif bot.sensor_state['oi mode'] == create_dict["SAFE"]:
                            dashboard.mode.set("Safe")
                        elif bot.sensor_state['oi mode'] == create_dict["FULL"]:
                            dashboard.mode.set("Full")
                        else:
                            dashboard.mode.set("")

                        if dashboard.modeflag.get() == True:
                            if dashboard.chgmode.get() == 'Passive':
                                bot.digit_led_ascii('    ')  # clear DSEG before Passive mode
                                bot.start()
                            elif dashboard.chgmode.get() == 'Safe':
                                bot.safe()
                            elif dashboard.chgmode.get() == 'Full':
                                bot.full()
                            elif dashboard.chgmode.get() == 'Seek Dock':
                                bot.digit_led_ascii('DOCK')  # clear DSEG before Passive mode
                                bot.start()
                                bot.seek_dock()
                            dashboard.modeflag.set(False)


                        # BATTERY
                        dashboard.voltage.set(str(round(bot.sensor_state['voltage']/1000,1)))
                        dashboard.current.set(str(abs(bot.sensor_state['current'])))
                        dashboard.capacity.set(str(bot.sensor_state['battery charge']))
                        dashboard.temp.set(str(bot.sensor_state['temperature']))
                        # Below outputs the value of battery charge
                        # csvfile = "</home/pi/roomba/IDLE>"
                        with open('battery.csv', "a") as output:
                            bat = str(bot.sensor_state['battery charge'])
                            fieldnames = ['var1']
                            writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator='\n')
                            # writer.writeheader()
                            writer.writerow({'var1': bat})
                        # print(str(bot.sensor_state['battery charge']))
                                
                        if bot.sensor_state['charging state'] == create_dict["NOT CHARGING"]:
                            dashboard.pbCurrent.configure(style="orange.Horizontal.TProgressbar")
                            dashboard.lblCurrent.configure(text="mA Load")
                            battcharging = False
                        elif bot.sensor_state['charging state'] == create_dict["RECONDITIONING"]:
                            dashboard.pbCurrent.configure(style="blue.Horizontal.TProgressbar")
                            dashboard.lblCurrent.configure(text="mA Recond")
                            #docked = True
                            battcharging = True
                        elif bot.sensor_state['charging state'] == create_dict["FULL CHARGING"]:
                            dashboard.pbCurrent.configure(style="green.Horizontal.TProgressbar")
                            dashboard.lblCurrent.configure(text="mA Charging")
                            #docked = True
                            battcharging = True
                        elif bot.sensor_state['charging state'] == create_dict["TRICKLE CHARGING"]:
                            dashboard.pbCurrent.configure(style="green.Horizontal.TProgressbar")
                            dashboard.lblCurrent.configure(text="mA Charging")
                            #docked = True
                            battcharging = True
                        elif bot.sensor_state['charging state'] == create_dict["WAITING"]:
                            dashboard.pbCurrent.configure(style="blue.Horizontal.TProgressbar")
                            dashboard.lblCurrent.configure(text="mA Waiting")
                            battcharging = False
                        elif bot.sensor_state['charging state'] == create_dict["CHARGE FAULT"]:
                            dashboard.pbCurrent.configure(style="red.Horizontal.TProgressbar")
                            dashboard.lblCurrent.configure(text="mA Fault")
                            battcharging = False

                        if bot.sensor_state['battery charge'] < 1000:
                            dashboard.pbCapacity.configure(style="red.Horizontal.TProgressbar")
                        else:
                            dashboard.pbCapacity.configure(style="orange.Horizontal.TProgressbar")

                        if bot.sensor_state['charging sources available']['home base']:
                            docked = True
                        else:
                            docked = False


                        # BUMPERS AND WHEEL DROP
                        if bot.sensor_state['wheel drop and bumps']['bump left'] == True:
                            dashboard.rbul.configure(state=NORMAL)
                            dashboard.rbul.select()
                        else:
                            dashboard.rbul.configure(state=DISABLED)
                                        
                        if bot.sensor_state['wheel drop and bumps']['bump right'] == True:
                            dashboard.rbur.configure(state=NORMAL)
                            dashboard.rbur.select()
                        else:
                            dashboard.rbur.configure(state=DISABLED)
                                        
                        if bot.sensor_state['wheel drop and bumps']['drop left'] == True:
                            dashboard.rbdl.configure(state=NORMAL)
                            dashboard.rbdl.select()
                        else:
                            dashboard.rbdl.configure(state=DISABLED)
                                        
                        if bot.sensor_state['wheel drop and bumps']['drop right'] == True:
                            dashboard.rbdr.configure(state=NORMAL)
                            dashboard.rbdr.select()
                        else:
                            dashboard.rbdr.configure(state=DISABLED)


                        # MOTORS
                        dashboard.leftmotor.set(str(bot.sensor_state['left motor current']))
                        dashboard.rightmotor.set(str(bot.sensor_state['right motor current']))


                        # DRIVE
                        if dashboard.driven.get() == 'Button\ndriven':
                            dashboard.canvas.place(x=474, y=735)
                            if dashboard.driveforward == True:
                                bot.drive(int(dashboard.speed.get()), 32767)
                            elif dashboard.drivebackward == True:
                                bot.drive(int(dashboard.speed.get()) * -1, 32767)
                            elif dashboard.driveleft == True:
                                bot.drive(int(dashboard.speed.get()), 1)
                            elif dashboard.driveright == True:
                                bot.drive(int(dashboard.speed.get()), -1)
                            else:
                                bot.drive(0, 32767)
                        else:
                            if dashboard.chgmode.get() == 'Seek Dock':
                                dashboard.canvas.place(x=474, y=735)
                            else:
                                dashboard.canvas.place(x=474, y=35)
                                
                            if dashboard.leftbuttonclick.get() == True:
                                bot.drive(dashboard.commandvelocity, dashboard.commandradius)
                            else:
                                bot.drive(0, 32767)


                        # TELEMETRY
                        vel = bot.sensor_state['requested velocity']
                        if vel <= 500: # forward
                            dashboard.velocity.set(str(vel))
                        else:          # backward
                            dashboard.velocity.set(str((65536-vel)*-1))
                            
                        rad = bot.sensor_state['requested radius']
                        if rad == 32767 or rad == 32768:
                            dashboard.radius.set("0")
                        elif rad <= 2000:
                            dashboard.radius.set(str(rad))
                        else:
                            dashboard.radius.set(str((65536-rad)*-1))
                            
                        dashboard.angle.set(str(bot.sensor_state['angle']))

                        if abs(bot.sensor_state['distance']) > 5: docked = False 
                        dist = dist + abs(bot.sensor_state['distance'])
                        dashboard.odometer.set(str(dist))


                        # WALL AND CLIFF SIGNALS
                        if bot.sensor_state['cliff left'] == True:
                            dashboard.rbcl.configure(state=NORMAL)
                            dashboard.rbcl.select()
                        else:
                            dashboard.rbcl.configure(state=DISABLED)

                        if bot.sensor_state['cliff front left'] == True:
                            dashboard.rbcfl.configure(state=NORMAL)
                            dashboard.rbcfl.select()
                        else:
                            dashboard.rbcfl.configure(state=DISABLED)

                        if bot.sensor_state['cliff front right'] == True:
                            dashboard.rbcfr.configure(state=NORMAL)
                            dashboard.rbcfr.select()
                        else:
                            dashboard.rbcfr.configure(state=DISABLED)

                        if bot.sensor_state['cliff right'] == True:
                            dashboard.rbcr.configure(state=NORMAL)
                            dashboard.rbcr.select()
                        else:
                            dashboard.rbcr.configure(state=DISABLED)

                        if bot.sensor_state['wall seen'] == True:
                            dashboard.rbw.configure(state=NORMAL)
                            dashboard.rbw.select()
                        else:
                            dashboard.rbw.configure(state=DISABLED)

                        if bot.sensor_state['virtual wall'] == True:
                            dashboard.rbvw.configure(state=NORMAL)
                            dashboard.rbvw.select()
                        else:
                            dashboard.rbvw.configure(state=DISABLED)


                        # LIGHT BUMPERS
                        b = 0
                        if bot.sensor_state['light bumper']['right'] == True:
                            b = b + 1
                        if bot.sensor_state['light bumper']['front right'] == True:
                            b = b + 2
                        if bot.sensor_state['light bumper']['center right'] == True:
                            b = b + 4
                        if bot.sensor_state['light bumper']['center left'] == True:
                            b = b + 8
                        if bot.sensor_state['light bumper']['front left'] == True:
                            b = b + 16
                        if bot.sensor_state['light bumper']['left'] == True:
                            b = b + 32
                        dashboard.lightbump.set(format(b, '06b'))
                        dashboard.lightbumpleft.set(str(bot.sensor_state['light bump left signal']))
                        dashboard.lightbumpfleft.set(str(bot.sensor_state['light bump front left signal']))
                        dashboard.lightbumpcleft.set(str(bot.sensor_state['light bump center left signal']))
                        dashboard.lightbumpcright.set(str(bot.sensor_state['light bump center right signal']))
                        dashboard.lightbumpfright.set(str(bot.sensor_state['light bump front right signal']))
                        dashboard.lightbumpright.set(str(bot.sensor_state['light bump right signal']))


                        # 7 SEGMENT DISPLAY
                        #bot.digit_led_ascii("abcd")
                        if dashboard.ledsource.get() == 'test':
                            bot.digit_led_ascii(dashboard.DSEG.get().rjust(4))  # rjustify and pad to 4 chars
                        elif dashboard.ledsource.get() == 'mode':
                            bot.digit_led_ascii(dashboard.mode.get()[:4].rjust(4))  # rjustify and pad to 4 chars
                                
                        dashboard.master.update() # inner loop to update dashboard telemetry

                except Exception: #, e:
                    # print "Aborting telemetry loop"
                    # print sys.stderr, "Exception: %s" % str(e)
                    traceback.print_exc(file=sys.stdout)
                    break
                    
        dashboard.master.update()
        time.sleep(0.5)   # outer loop to handle data link retry connect attempts
        
    # a Power() command will stop serial communication and the OI will enter into Passive mode.
    # a Stop() command will stop serial communication and the OI will enter into Off mode.
    # iRobot beeps once to acknowledge it is starting from Off mode when undocked
    if bot.SCI.ser.isOpen(): bot.power()
    GPIO.cleanup()
    dashboard.master.destroy()  # exitflag = True


def main():

    # declare objects
    root = Tk()
    
    dashboard=Dashboard(root)                       # paint GUI
    RetrieveCreateTelemetrySensors(dashboard)       # comms with iRobot
    #bigbatts()

    # root.update_idletasks() # does not block code execution
    # root.update([msecs, function]) is a loop to run function after every msec
    # root.after(msecs, [function]) execute function after msecs
    root.mainloop() # blocks. Anything after mainloop() will only be executed after the window is destroyed
    

if __name__ == '__main__':
    auklet_monitoring = Monitoring("eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiYWRjYjRiNGQtMDliOC00MWE5LTk5NzAtMGI5YWUwNzA3ZjlhIiwidXNlcm5hbWUiOiI1ODBjMmNkNS00Mzg2LTRkNDYtOGNmMi03NWY3ZjMxYjY1NTAiLCJleHAiOjE1MzA5MDAzNTcsImVtYWlsIjoiIn0.aJ_K4D8fFCprWDajtdA6qJD3KIETnOyBGnNauNT3BY0", "qXa285XCSPnQTk7aYXe5TN", monitoring=True)
    auklet_monitoring.start()
    main()
    auklet_monitoring.stop()
