#!/usr/bin/python

"""
iRobot Create 2 Drive
Dec 2016

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
    import RPi.GPIO as GPIO # BRC pin pulse


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
        print "Forward"
        self.driveforward = True

    def on_press_drivebackward(self, event):
        print "Backward"
        self.drivebackward = True

    def on_press_driveleft(self, event):
        print "Left"
        self.driveleft = True

    def on_press_driveright(self, event):
        print "Right"
        self.driveright = True

    def on_press_stop(self, event):
        print "Stop"
        self.driveforward = False
        self.drivebackward = False
        self.driveleft = False
        self.driveright = False

    def on_keypress(self, event):
        print "Key pressed ", repr(event.char)

    def on_leftkey(self, event):
        print "Left"
        self.driveleft = True

    def on_rightkey(self, event):
        print "Right"
        self.driveright = True

    def on_upkey(self, event):
        print "Forward"       
        self.driveforward = True
        
    def on_downkey(self, event):
        print "Backward"
        self.drivebackward = True

    def on_keyrelease(self, event):
        print "Stop"
        self.driveforward = False
        self.drivebackward = False
        self.driveleft = False
        self.driveright = False

    def on_leftbuttonclick(self, event):
        self.leftbuttonclick.set(True)
        self.xorigin = event.x
        self.yorigin = event.y
        self.commandvelocity = 0
        self.commandradius = 0
        #print str(event.x) + ":" + str(event.y)

    def on_leftbuttonrelease(self, event):
        self.leftbuttonclick.set(False)

    def on_motion(self, event):
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
        print "Exiting irobot-drive"
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
        self.modeflag.set(True)
        print "OI mode change from " +  self.mode.get() + " to " + self.chgmode.get()
            
    def InitialiseVars(self):
        # declare variable classes=StringVar, BooleanVar, DoubleVar, IntVar
        self.dataconn = BooleanVar() ; self.dataconn.set(True)   # Attempt a data link connection with iRobot
        self.dataretry = BooleanVar(); self.dataretry.set(False) # Retry a data link connection with iRobot
        self.chgmode = StringVar()   ; self.chgmode.set('')      # Change OI mode
        self.chgmode.trace('w', self.on_mode_change)             # Run function when value changes
        self.modeflag = BooleanVar() ; self.modeflag.set(False)  # Request to change OI mode
        self.mode = StringVar()                                  # Current operating OI mode
        
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

        self.exitflag = BooleanVar() ; self.exitflag = False     # Exit program flag

    def paintGUI(self):
        
        self.master.geometry('350x260+320+200')
        self.master.wm_title("iRobot Drive")
        self.master.configure(background='white')
        self.master.protocol("WM_DELETE_WINDOW", self.on_exit)

        s = ttk.Style()
        # theme=CLAM,ALT,CLASSIC,DEFAULT
        s.theme_use('clam')


        # TOP FRAME - DATA LINK
        frame = Frame(self.master, bd=1, width=330, height=100, background='white', relief=GROOVE)

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

        # telemetry display
        label = Label(frame, textvariable=self.mode, anchor=W, background='snow2', width=10)
        label.pack()
        label.place(x=150, y=33)

        # combobox
        self.cmbMode = ttk.Combobox(frame, values=('Off', 'Passive', 'Safe', 'Full', 'Seek Dock'), textvariable=self.chgmode, width=10)
        #self.cmbMode['values'] = ('Off', 'Passive', 'Safe', 'Full', 'Seek Dock')
        self.cmbMode.pack()
        self.cmbMode.place(x=150,y=65)      
        
        #frame.pack()
        frame.pack_propagate(0) # prevents frame autofit
        frame.place(x=10, y=10)


        # BOTTOM FRAME - DRIVE
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
        self.scale.set(25)

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
        frame.place(x=10, y=120)

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

            print "Attempting data link connection"
            dashboard.comms_check(-1)
            dashboard.master.update()
            
            bot = create2api.Create2()
            bot.digit_led_ascii('    ') # clear DSEG before Passive mode
            print "Issuing a Start()"
            bot.start()                 # issue passive mode command
            #bot.safe()
            dist = 0                    # reset odometer
            connection_attempt += 1

            while True and not dashboard.exitflag:
                        
                try:
                    # check if serial is communicating
                    time.sleep(.3)
                    if timelimit(3, bot.get_packet, (100, ), {}) == False:  # run bot.get_packet(35) with a timeout

                        print "Data link down"
                        dashboard.comms_check(0)
                        bot.destroy()
                        if connection_attempt > 5:
                            connection_attempt = 0
                            print "Attempted 6 communication connections... sleeping for 6 mins..."
                            time.sleep(360)
                        print "Simulating a Clean button press"
                        GPIO.output(CLNpin, GPIO.HIGH) # Single press of Clean button enters Passive mode
                        time.sleep(.2)
                        GPIO.output(CLNpin, GPIO.LOW)  # Clean button activates on button 'release'
                        dashboard.dataconn.set(True)
                        break

                    else:
                        
                        # DATA LINK
                        connection_attempt = 0
                        if dashboard.dataconn.get() == True:
                            print "Data link up"
                            dashboard.dataconn.set(False)

                        if dashboard.dataretry.get() == True:   # retry an unstable (green) connection
                            print "Data link reconnect"
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
                            print 'BRC pin pulse'
                            BtnTimer = datetime.datetime.now() + datetime.timedelta(seconds=30)
                            if docked:
                                print 'Dock'
                                bot.buttons(4) # 1=Clean 2=Spot 4=Dock 8=Minute 16=Hour 32=Day 64=Schedule 128=Clock
                            # switch to safe mode if undocked and detects OI mode is Passive
                            # (no longer required with Clean button press simulation)
                            elif bot.sensor_state['oi mode'] == create_dict["PASSIVE"] and \
                                 dashboard.chgmode.get() != 'Seek Dock':
                                dashboard.chgmode.set('Safe') 
                                bot.safe()
                                                 
                        if bot.sensor_state['oi mode'] == create_dict["OFF"]:
                            dashboard.mode.set("Off")
                        elif bot.sensor_state['oi mode'] == create_dict["PASSIVE"]:
                            dashboard.mode.set("Passive")
                        elif bot.sensor_state['oi mode'] == create_dict["SAFE"]:
                            dashboard.mode.set("Safe")
                        elif bot.sensor_state['oi mode'] == create_dict["FULL"]:
                            dashboard.mode.set("Full")
                        else:
                            dashboard.mode.set("")

                        if dashboard.modeflag.get() == True:
                            if dashboard.chgmode.get() == 'Off':
                                bot.digit_led_ascii('    ')  # clear DSEG before Off mode
                                bot.stop()
                            elif dashboard.chgmode.get() == 'Passive':
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

                        if bot.sensor_state['charging sources available']['home base']:
                            docked = True
                        else:
                            docked = False

                        # DRIVE
                        if dashboard.driven.get() == 'Button\ndriven':
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
                            if dashboard.leftbuttonclick.get() == True:
                                bot.drive(dashboard.commandvelocity, dashboard.commandradius)
                            else:
                                bot.drive(0, 32767)

                        # 7 SEGMENT DISPLAY
                        #bot.digit_led_ascii("abcd")
                        bot.digit_led_ascii(dashboard.mode.get()[:4].rjust(4))  # rjustify and pad to 4 chars
                                
                        dashboard.master.update() # inner loop to update dashboard telemetry

                except Exception: #, e:
                    print "Aborting telemetry loop"
                    #print sys.stderr, "Exception: %s" % str(e)
                    traceback.print_exc(file=sys.stdout)
                    break
                    
        dashboard.master.update()
        time.sleep(1)   # outer loop to handle data link retry connect attempts
        
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

    # root.update_idletasks() # does not block code execution
    # root.update([msecs, function]) is a loop to run function after every msec
    # root.after(msecs, [function]) execute function after msecs
    root.mainloop() # blocks. Anything after mainloop() will only be executed after the window is destroyed
    

if __name__ == '__main__': 
    main()
    
