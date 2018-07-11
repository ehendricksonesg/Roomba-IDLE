#!/bin/bash
#
# Raspberry Pi onboard LED control.
#
# This script controls the onboard Raspberry Pi LEDs for the Raspberry Pi 2 and later models. Older 
# models' PWR LEDs are hard-wired, so you'll have to grab a soldering iron if you want to control them
# :-)
#
# (Optional) Turn on (1) or off (0) the PWR LED
#echo 1 | tee /sys/class/leds/led0/brightness
echo 0 | tee /sys/class/leds/led0/brightness
