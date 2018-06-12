import create2api
import json   # We'll use this to format the output
import time

bot = create2api.Create2()

print "Issuing Start command"
bot.start() # passive mode
print "Issuing mode command"
#bot.power()
bot.safe()
#bot.full()

time.sleep(1)

#print '==============Start Up Data=============='
#print json.dumps(bot.sensor_state, indent=4)

#print '========================================='
#print ''

#Packet 100 contains all sensor data.
#bot.get_packet(100)

#print '==============Updated Sensors=============='
#print json.dumps(bot.sensor_state, indent=4, sort_keys=False)

i = 1
while i<=10:
    print "Requesting packets from OI"
    bot.get_packet(100)
    print "[" + str(i) + "]"
    print "Charging State: " + str(bot.sensor_state['charging state'])
    print "Voltage: " + str(bot.sensor_state['voltage'])
    print "Temperature: " + str(bot.sensor_state['temperature'])
    print "OI Mode: " + str(bot.sensor_state['oi mode'])
    print "Cliff Left: " + str(bot.sensor_state['cliff left'])
    print "Light Bump Left Signal: " + str(bot.sensor_state['light bump left signal'])
    if bot.sensor_state['oi mode'] != 2:
        print "OI mode is not safe"
        if i > 5:
            print "Attempting to set mode to Safe"
            bot.safe()
            time.sleep(3)
    print " "
    time.sleep(.3)
    i+=1
    
bot.reset()  # off mode
##bot.stop()   # off mode
#bot.power()  # passive mode

#time.sleep(2)
#i = 1
#while i <= 60:
#    time.sleep(1)
#    print "[" + str(i) + "]"
#    bot.start()
#    i+=1
