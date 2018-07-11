import serial
import time

# Open a serial connection to Roomba
ser = serial.Serial(port='/dev/ttyAMA0', baudrate=115200)

# Assuming the robot is awake, start safe mode so we can hack.
ser.write('\x83')
time.sleep(.1)

# Program a five-note start song into Roomba.
#########ser.write('\x8c\x00\x18E\x10E\x10E\x20E\x10E\x10E\x20E\x10G\x10C\x10D\x10E\x40F\x10F\x10F\x10F\x10F\x10E\x10E\x10E\x10G\x10G\x10F\x10D\x10C\x40')
#ser.write('\x8c\x00\x10E\x10E\x10E\x20E\x10E\x10E\x20E\x20G\x10C\x10D\x10E\x20F\x10F\x10F\x10F\x20F\x20')
#ser.write('\x8c\x01\x05C\x10H\x18J\x08L\x10O\x20')
ser.write('\x8c\x00\x02G\x10C\x20')

#ser.write('\x8c\x01\x0dF\x10F\x10F\x10F\x10F\x10E\x10E\x10E\x10G\x10G\x10F\x10D\x10C\x40')
#ser.write('\x8c\x01\x18E\x10E\x10E\x20E\x10E\x10E\x20E\x10G\x10C\x10D\x10E\x40F\x10F\x10F\x10F\x10F\x10E\x10E\x10E\x10G\x10G\x10F\x10D\x10C\x40')

# Play the song we just programmed.
ser.write('\x8d\x00')
#ser.write('\x8d\x01')
time.sleep(2) # wait for the song to complete

# Leave the Roomba in passive mode; this allows it to keep
#  running Roomba behaviors while we wait for more commands.
ser.write('\x80')

# Close the serial port; we're done for now.
ser.close()
