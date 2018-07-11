#!/usr/bin/env python
# 13 January 2015

###########################################################################
# Copyright (c) 2014 iRobot Corporation http://www.irobot.com/
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided 
# that the following conditions are met:
#
#   Redistributions of source code must retain the above copyright notice, this list of conditions and 
#   the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright notice, this list of conditions and 
#   the following disclaimer in the documentation and/or other materials provided with the distribution.
#
#   Neither the name of iRobot Corporation nor the names of its contributors may be used to endorse or 
#   promote products derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED 
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A 
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR 
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT 
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR 
# TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF 
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
###########################################################################

# A admittedly rough-around-the-edges script to generate raw serial commands 
# to send over a socket for controlling a Create. 
# Only supports unidirectional communication. The robot won't move if it's not 
# in safe mode. To drive, click and drag in the window. 

# Be sure to change the HOST variable below to your robot's IP address or 
# hostname! If you don't, it'll crash and burn upon sending the first command.
 
import socket 
import struct 
from Tkinter import * 
from time import sleep 
from threading import Lock 

VERBOSE = False # change this to True to see the raw commands sent 

WIDTH = 100 # window width 
HEIGHT = 100 # window height 

ROTMAX = 100 # max rotational rate (deg/s) 
TRANSMAX = 300 # max translational rate (mm/s) 

DEADZONE = 0.1 # percent of the screen to go straight 
RATELIMIT = 0.2 # number of seconds between each drive command 

HOST = '192.168.0.120' # your robot IP or hostname  
PORT = 9999 

print HOST, PORT 
print ">P<assive, >S<afe, >F<ull, >C<lean, >D<ock, space = beep"
print "If nothing happens, try pressing 'P' and then 'S' to get into safe mode." 

mutex = Lock()
 
root = Tk()

# Sends a raw command to the Create via a socket.
def serCmd(data):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    sock.sendall(data)
    sock.close()
    if VERBOSE == True:
        tmp = ''
        for c in data:
            tmp += hex(ord(c)).rsplit('x')[1]
        print tmp

# Decides on a motion command based on the location of the mouse when a button is pressed, and then sends 
# it to the robot.
def callbackMouseDown(event):
    if (mutex.acquire(False)):
        trans = float((HEIGHT / 2) - event.y) / (HEIGHT / 2)
        rot = float((WIDTH / 2) - event.x) / (WIDTH / 2)

        if rot > 1.0:
            rot = 1.0
        if rot < -1.0:
            rot = -1.0
        if abs(rot) < DEADZONE:
            rot = 0
            
        if trans > 1.0:
            trans = 1.0
        if trans < -1.0:
            trans = -1.0

        vl = int(trans * TRANSMAX + rot * ROTMAX);
        vr = int(trans * TRANSMAX - rot * ROTMAX);

        x = struct.pack(">Bhh", 0x91, vl, vr)
        serCmd(x)
        sleep(RATELIMIT) # rate limiting
        mutex.release()
    
# Stops the robot when the mouse button is released.
def callbackMouseUp(event):
    serCmd("\x89\x00\x00\x00\x00") # stop

# A small handler for keyboard events. Feel free to add more!
def callbackKey(event):
    c = event.char.upper()

    if c == 'P': # Passive
        serCmd('\x80')
    elif c == 'S': # Safe
        serCmd('\x83')
    elif c == 'F': # Full
        serCmd('\x84')
    elif c == 'C': # Clean
        serCmd('\x87')
    elif c == 'D': # Dock
        serCmd('\x8f')
    elif c == ' ': # Beep
        serCmd('\x8c\x03\x01\x40\x10\x8d\x03') 

frame = Frame(root, width=WIDTH, height=HEIGHT) 
frame.bind("<Button-1>", callbackMouseDown) 
frame.bind("<B1-Motion>", callbackMouseDown) 
frame.bind("<ButtonRelease-1>", callbackMouseUp) 
root.bind("<Key>", callbackKey) 
frame.pack()

root.mainloop()
