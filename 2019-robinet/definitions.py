import time
import machine
import os
import utime
import ntptime
from machine import Timer
from logger import log
import sys

DISCONNECTED = 0
CONNECTING = 1
CONNECTED = 2

# function(eventName)
onWlanEvent = None

def emitWlanEvent(event):
	try:
		if onWlanEvent:
			onWlanEvent(event);
	except Exception as e:
		log("Error in 'onWlanEvent' handler: " + str(e));	
		sys.print_exception(e);

def onUnloadModule():
	blinkTimer.deinit();
	global wasConnected;
	wasConnected = None
			
def do_connect(ssid, password):
	import network
	global wlan;
	network.WLAN(network.AP_IF).active(False)
	wlan = network.WLAN(network.STA_IF)
	wlan.active(True)
	if not wlan.isconnected():
		log('Connecting to network ' + ssid + '...')
		wlan.connect(ssid, password)
		emitWlanEvent(CONNECTING)

def blink():
	global wasConnected;
	global firstConnectionSucceded;
	
	connected = wlan.isconnected();
	pinLed.value(not pinLed.value());
	
	period = -1;
	if not connected and (wasConnected == None or wasConnected):
		period = 100;
		if wasConnected != None:
			log('Disconnected from network');
			emitWlanEvent(DISCONNECTED)
	elif connected and (wasConnected == None or not wasConnected):
		period = 500;
		log('Connected to network. IP = ' + str(wlan.ifconfig()[0]));
		firstConnectionSucceded = True;
		emitWlanEvent(CONNECTED)
	wasConnected = connected;
	
	if period > 0:
		blinkTimer.init(period=period, mode=Timer.PERIODIC, callback=lambda t:blink());
	# else status not changed; so we don't change the timer

pinLed = machine.Pin(2, machine.Pin.OUT);
blinkTimer = Timer(-1);
wasConnected = None;
firstConnectionSucceded = False;
wlan = None;

import esp
esp.sleep_type(esp.SLEEP_NONE)

