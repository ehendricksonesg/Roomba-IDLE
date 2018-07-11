#!/usr/bin/env python
# 09 December 2014

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

# A admittedly rough-around-the-edges script to receive raw serial commands over a socket and then send 
# them to the serial port for controlling Create. Only supports unidirectional communication. The robot 
# won't move if it's not in safe or full mode. To drive, click and drag in the window. 

# Be sure the account running this has the privileges to use the serial port. 
# On Linux, that usually means it must belong to the 'dialout' group.

import socket 
import serial 

HOST = '' 
PORT = 9999

# Open a socket.
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
sock.bind((HOST, PORT)) 
sock.listen(1) 
print "Listening on port " + str(PORT)

# Open a serial connection to Roomba.
ser = serial.Serial(port='/dev/ttyAMA0', baudrate=115200) 

try:
    while True: # wait for socket to connect
        conn, addr = sock.accept()
        print '%s:%s connected.' % addr

        while True:
            try:
                data = conn.recv(1024)
            except Exception:
                print "Ran out of data."
                data = False
            if not data:
                break
            print len(data), data.encode("hex"),
            # do something with the data here
            ser.write(data)
        conn.close()
        print '%s:%s disconnected.' % addr
        
except Exception:
    sock.shutdown(socket.SHUT_RDWR)
    sock.close()
    ser.close()
    print "Goodbye."
