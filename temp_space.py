"""
This file was used as a space for cut and paste.
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
    import RPi.GPIO as GPIO  # BRC pin pulse
    import csv


class Dashboard:

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
        print
        "Forward"
        self.driveforward = True

    def on_press_drivebackward(self, event):
        print
        "Backward"
        self.drivebackward = True

    def on_press_driveleft(self, event):
        print
        "Left"
        self.driveleft = True

    def on_press_driveright(self, event):
        print
        "Right"
        self.driveright = True

    def on_press_stop(self, event):
        print
        "Stop"
        self.driveforward = False
        self.drivebackward = False
        self.driveleft = False
        self.driveright = False

    def on_keypress(self, event):
        print
        "Key pressed ", repr(event.char)

    def on_leftkey(self, event):
        print
        "Left"
        self.driveleft = True

    def on_rightkey(self, event):
        print
        "Right"
        self.driveright = True

    def on_upkey(self, event):
        print
        "Forward"
        self.driveforward = True

    def on_downkey(self, event):
        print
        "Backward"
        self.drivebackward = True

    def on_keyrelease(self, event):
        print
        "Stop"
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
        # print str(event.x) + ":" + str(event.y)

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

        # print str(self.xorigin - event.x) + ":" + str(self.yorigin - event.y)
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

        # print 'iRobot velocity, radius is ' + str(self.commandvelocity) + "," + str(self.commandradius)

    def getangle(self, event):
        dx = event.x - origin[0]
        dy = event.y - origin[1]
        try:
            return complex(dx, dy) / abs(complex(dx, dy))
        except ZeroDivisionError:
            return 0.0  # cannot determine angle

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
        # if messagebox.askokcancel("Quit", "Do you want to quit?"):
        print
        "Exiting irobot-dashboard"
        os.system('set -r on')  # turn on auto repeat key
        self.exitflag = True
        # GPIO.cleanup()
        # self.master.destroy()

    def on_select_datalinkconnect(self):
        if self.rbcomms.cget('selectcolor') == 'red':
            self.dataconn.set(True)
        elif self.rbcomms.cget('selectcolor') == 'lime green':
            self.dataretry.set(True)

    def on_mode_change(self, *args):
        self.ledsource.set('mode')
        self.modeflag.set(True)
        print
        "OI mode change from " + self.mode.get() + " to " + self.chgmode.get()

    def on_led_change(self, *args):
        self.ledsource.set('test')

    def InitialiseVars(self):
        # declare variable classes=StringVar, BooleanVar, DoubleVar, IntVar
        self.voltage = StringVar();
        self.voltage.set('0')  # Battery voltage (mV)
        self.current = StringVar();
        self.current.set('0')  # Battery current in or out (mA)
        self.capacity = StringVar();
        self.capacity.set('0')  # Battery capacity (mAh)
        self.temp = StringVar();
        self.temp.set('0')  # Battery temperature (Degrees C)

        self.dataconn = BooleanVar();
        self.dataconn.set(True)  # Attempt a data link connection with iRobot
        self.dataretry = BooleanVar();
        self.dataretry.set(False)  # Retry a data link connection with iRobot
        self.chgmode = StringVar();
        self.chgmode.set('')  # Change OI mode
        self.chgmode.trace('w', self.on_mode_change)  # Run function when value changes
        self.modeflag = BooleanVar();
        self.modeflag.set(False)  # Request to change OI mode
        self.mode = StringVar()  # Current operating OI mode
        self.TxVal = StringVar();
        self.TxVal.set('0')  # Num transmitted packets

        self.leftmotor = StringVar();
        self.leftmotor.set('0')  # Left motor current (mA)
        self.rightmotor = StringVar();
        self.rightmotor.set('0')  # Left motor current (mA)

        self.speed = StringVar()  # Maximum drive speed
        self.driveforward = BooleanVar();
        self.driveforward.set(False)
        self.drivebackward = BooleanVar();
        self.drivebackward.set(False)
        self.driveleft = BooleanVar();
        self.driveleft.set(False)
        self.driveright = BooleanVar();
        self.driveright.set(False)
        self.leftbuttonclick = BooleanVar();
        self.leftbuttonclick.set(False)
        self.commandvelocity = IntVar();
        self.commandvelocity.set(0)
        self.commandradius = IntVar();
        self.commandradius.set(0)
        self.driven = StringVar();
        self.driven.set('Button\ndriven')
        self.xorigin = IntVar();
        self.xorigin = 0  # mouse x coord
        self.yorigin = IntVar();
        self.yorigin = 0  # mouse x coord

        self.velocity = StringVar();
        self.velocity.set('0')  # Velocity requested (mm/s)
        self.radius = StringVar();
        self.radius.set('0')  # Radius requested (mm)
        self.angle = StringVar();
        self.angle.set('0')  # Angle in degrees turned since angle was last requested
        self.odometer = StringVar();
        self.odometer.set('0')  # Distance traveled in mm since distance was last requested

        self.lightbump = StringVar();
        self.lightbump.set('0')
        self.lightbumpleft = StringVar();
        self.lightbumpleft.set('0')
        self.lightbumpfleft = StringVar();
        self.lightbumpfleft.set('0')
        self.lightbumpcleft = StringVar();
        self.lightbumpcleft.set('0')
        self.lightbumpcright = StringVar();
        self.lightbumpcright.set('0')
        self.lightbumpfright = StringVar();
        self.lightbumpfright.set('0')
        self.lightbumpright = StringVar();
        self.lightbumpright.set('0')

        self.DSEG = StringVar()  # 7 segment display
        self.DSEG.trace('w', self.on_led_change)  # Run function when value changes
        self.ledsource = StringVar();
        self.ledsource.set('mode')  # Determines what data to display on DSEG

        self.exitflag = BooleanVar();
        self.exitflag = False  # Exit program flag

    def paintGUI(self):
        # Window creation
        self.master.geometry('300x300')
        self.master.wm_title("Roomba Drain")
        self.master.configure(background='aquamarine')
        self.master.protocol("WM_DELETE_WINDOW", self.on_exit)
        # Styles
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
        # label.place(x=230, y=32)
        self.lblCurrent = Label(frame, text="mA", background='white')
        self.lblCurrent.pack()
        # self.lblCurrent.place(x=230, y=52)
        label = Label(frame, text="mAH Capacity", background='white')
        label.pack()
        # label.place(x=230, y=72)
        label = Label(frame, text="Temp 'C", background='white')
        label.pack()
        # label.place(x=230, y=92)

        # telemetry display
        label = Label(frame, textvariable=self.voltage, font=("DSEG7 Classic", 16), anchor=E, background='white',
                      width=4)
        label.pack()
        # label.place(x=170, y=30)
        label = Label(frame, textvariable=self.current, font=("DSEG7 Classic", 16), anchor=E, background='white',
                      width=4)
        label.pack()
        # label.place(x=170, y=50)
        label = Label(frame, textvariable=self.capacity, font=("DSEG7 Classic", 16), anchor=E, background='white',
                      width=4)
        label.pack()
        # label.place(x=170, y=70)
        label = Label(frame, textvariable=self.temp, font=("DSEG7 Classic", 16), anchor=E, background='white', width=4)
        label.pack()
        # label.place(x=170, y=90)

        # progress bars
        pb = ttk.Progressbar(frame, variable=self.voltage, style="orange.Horizontal.TProgressbar", orient="horizontal",
                             length=150, mode="determinate")
        pb["maximum"] = 20
        # pb["value"] = 15
        pb.pack()
        # pb.place(x=10, y=31)
        self.pbCurrent = ttk.Progressbar(frame, variable=self.current, style="orange.Horizontal.TProgressbar",
                                         orient="horizontal", length=150, mode="determinate")
        self.pbCurrent["maximum"] = 1000
        # self.pbCurrent["value"] = 600
        self.pbCurrent.pack()
        # self.pbCurrent.place(x=10, y=51)
        self.pbCapacity = ttk.Progressbar(frame, variable=self.capacity, style="orange.Horizontal.TProgressbar",
                                          orient="horizontal", length=150, mode="determinate")
        self.pbCapacity["maximum"] = 3000
        # self.pbCapacity["value"] = 2000
        self.pbCapacity.pack()
        # self.pbCapacity.place(x=10, y=71)
        pb = ttk.Progressbar(frame, variable=self.temp, style="orange.Horizontal.TProgressbar", orient="horizontal",
                             length=150, mode="determinate")
        pb["maximum"] = 50
        # pb["value"] = 40
        pb.pack()
        # pb.place(x=10, y=91)

        # frame.pack()
        frame.pack_propagate(0)  # prevents frame autofit
        # frame.place(x=10, y=10)


def main():
    # declare objects
    root = Tk()

    dashboard = Dashboard(root)  # paint GUI
    # RetrieveCreateTelemetrySensors(dashboard)  # comms with iRobot
    # bigbatts()

    # root.update_idletasks() # does not block code execution
    # root.update([msecs, function]) is a loop to run function after every msec
    # root.after(msecs, [function]) execute function after msecs
    root.mainloop()  # blocks. Anything after mainloop() will only be executed after the window is destroyed


if __name__ == '__main__':
        main()
