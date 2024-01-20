import definitions as df
from logger import log
from pollingPin import PollingPin
from timesync import TimeSync
import machine
from machine import Timer, Pin, PWM
import utime
import gc

def onUnloadModule():
	timer.deinit()

log("Starting program")

import __main__
USE_BLINK = __main__.USE_BLINK
BLYNK_RETRY_INTERVAL_SEC = 60

# @see TimerManager. The current implementation needs that this is less then 1 min. However, I don't
# see why this should be bigger than 1 / a few secs
LOOP_TIMER_PERIOD_SEC = 1
# USE_BLINK is in boot.py

isIrigatie = False
with open("wifi_cfg.py") as f:
    exec(f.read(), globals())

enableTimeSync = True

def setEnableTimeSync(value):
	global enableTimeSync
	enableTimeSync = value

# D1
pinRobinet = machine.Pin(5, machine.Pin.OUT)
pinRobinetDirection = machine.Pin(0, machine.Pin.OUT)
pinRobinetDirection.on()

# pinRobinetClosed = machine.Pin(14, machine.Pin.IN, machine.Pin.PULL_UP)
# pinRobinetOpen = machine.Pin(12, machine.Pin.IN, machine.Pin.PULL_UP)
# D5
pinRobinetClosed = machine.Pin(14, machine.Pin.IN, None)
# D6
pinRobinetOpen = machine.Pin(12, machine.Pin.IN, None)
# D7
pinRobinetButon = machine.Pin(13, machine.Pin.IN, machine.Pin.PULL_UP)
dictPins = { "rob": pinRobinet, "inCls": pinRobinetClosed, "inOpn": pinRobinetOpen, "inBtn": pinRobinetButon }

# for pin in dictPins.values():
# 	pin.on()
# 	print(pin, pin.value())

valveState = 0 # 0 = moving unknown on start 1 = closing was open on start 2 = opening was closed on start
valveSecurityTimer = machine.Timer(-1)

def calculateValveState():
	global valveState
	if pinRobinetClosed.value() == 0:
		valveState = 2
		return "closed"
	elif pinRobinetOpen.value() == 0:
		valveState = 1
		return "open"
	else:
		valveState = 0
		return "unknown"

def startValveMotor():
	pinRobinetOpenPP.enable()
	pinRobinetClosedPP.enable()
	str = calculateValveState()
	pinRobinet.on() # start moving
	log("Valve started moving with state: " + str)
	valveSecurityTimer.init(period=30 * 1000, mode=machine.Timer.ONE_SHOT, callback=lambda t: (pinRobinet.off(), log("Valve error")))
	
def handleValveOpenOrClose():
	if (valveState == 0
			or valveState == 1 and pinRobinetClosed.value() == 0
			or valveState == 2 and pinRobinetOpen.value() == 0):
		pinRobinet.off()
		valveSecurityTimer.deinit()
		pinRobinetOpenPP.disable()
		pinRobinetClosedPP.disable()
		log("Valve stopped moving with state: " + calculateValveState())

from debouncer import Debouncer
		
# d1 = Debouncer(pinRobinetButon, startValveMotor)
# d2 = Debouncer(pinRobinetOpen, handleValveOpenOrClose)
# d3 = Debouncer(pinRobinetClosed, handleValveOpenOrClose)

timeSync = TimeSync(timeZoneOffsetSec = 0 * 3600)

def defineBlynkHandlers():
	@blynk.on("connected")
	def blynkConnected(ping):
		log('Blynk ready. Ping: ' + str(ping) + 'ms')

	@blynk.on("disconnected")
	def blynkDisconnected():
		log('Blynk disconnected')
		
	@blynk.on("readV10")
	def getStatus():
		now = utime.localtime()
		str = "{:02d}:{:02d}:{:02d} {}".format(now[3], now[4], now[5], calculateValveState())
		blynk.virtual_write(10, str)
		blynk.virtual_write(2, 255 if pinRobinetClosed.value() == 0 else 0)
		blynk.virtual_write(3, 255 if pinRobinetOpen.value() == 0 else 0)
		blynk.virtual_write(4, 255 if pinRobinet.value() == 1 else 0)

	# see in README.md pb 2022-08-23
	@blynk.on("V0")
	def switchValve(value):
		if value[0] == "1":
			startValveMotor()

	@blynk.on("V1")
	def execBlynkCommand(value):
		spl = value[0].split(" ")
		log("Exec blynk cmd {}".format(str(spl)))
		result = "Unknown command"
		c = spl[0]
		if c == "help":
			result = "Available commands: help, mem, valve, " + ", ".join(dictPins.keys())
		elif c == "mem":
			beforeC = gc.mem_free()
			gc.collect()
			result = "Free mem (before / after GC): {} / {}".format(beforeC, gc.mem_free())
		elif c == "valve":
			startValveMotor()
			result = "OK"
		elif c in dictPins:
			try:
				value = int(spl[1])
			except:
				result = "Number error"
			else:
				dictPins[c].value(value)
				result = "Pin value modified"
		blynk.virtual_write(1, result)

blynk = None
lastConnectAttempt = 0

def loop():
	try:
		if enableTimeSync:
			timeSync.syncIfNeeded()	
		if USE_BLINK and df.wlan.isconnected():
			import BlynkLib # was already imported in boot.py
			global blynk
			global lastConnectAttempt
			if not blynk:
				blynk = BlynkLib.Blynk(BLYNK_AUTH)
				defineBlynkHandlers()
			elif (blynk.state == BlynkLib.DISCONNECTED # may be CONNECTING, so this check is needed
					and utime.time() - lastConnectAttempt > BLYNK_RETRY_INTERVAL_SEC):
				lastConnectAttempt = utime.time()
				blynk.connect()
			blynk.run()
	finally:
		timer.init(period=LOOP_TIMER_PERIOD_SEC * 1000, mode=Timer.ONE_SHOT, callback=lambda t:loop())		
	
df.do_connect(WIFI_CONFIG[0], WIFI_CONFIG[1])
df.blink()

timer = Timer(-1)
loop()

pinRobinetButtonPP = PollingPin(pinRobinetButon, startValveMotor, 0, 50)
pinRobinetButtonPP.enabled = True
pinRobinetOpenPP = PollingPin(pinRobinetOpen, handleValveOpenOrClose)
pinRobinetClosedPP = PollingPin(pinRobinetClosed, handleValveOpenOrClose)

def pinPollingTimerHandler(timer):
	pinRobinetButtonPP.run()
	pinRobinetOpenPP.run()
	pinRobinetClosedPP.run()

pinPollingTimer = Timer(-1)
pinPollingTimer.init(period=50, mode=Timer.PERIODIC, callback=pinPollingTimerHandler)

