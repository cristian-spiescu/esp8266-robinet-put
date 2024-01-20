from timermanager import TimerManager, TimerConfig
import definitions as df
from logger import log
from timesync import TimeSync
import machine
from machine import Timer
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

isIrigatie = True
with open("wifi_cfg.py") as f:
    exec(f.read(), globals())

enableTimeSync = True

def setEnableTimeSync(value):
	global enableTimeSync
	enableTimeSync = value

if isIrigatie:
	# small issue: on boot, it is ON for a short while
	pinRotoare = machine.Pin(16, machine.Pin.OUT)
	pinPicurator = machine.Pin(5, machine.Pin.OUT)
	pinFoisor = machine.Pin(4, machine.Pin.OUT)
	pinStrada = machine.Pin(14, machine.Pin.OUT)
	dictPins = { "rot": pinRotoare, "pic": pinPicurator, "foi": pinFoisor, "str": pinStrada}
else:
	pinRobinet = machine.Pin(4, machine.Pin.OUT)
	pinRobinetClosed = machine.Pin(14, machine.Pin.IN, machine.Pin.PULL_UP)
	pinRobinetOpen = machine.Pin(12, machine.Pin.IN, machine.Pin.PULL_UP)
	pinRobinetButon = machine.Pin(13, machine.Pin.IN, machine.Pin.PULL_UP)
	dictPins = { "rob": pinRobinet, "inCls": pinRobinetClosed, "inOpn": pinRobinetOpen, "inBtn": pinRobinetButon }

for pin in dictPins.values():
	if isIrigatie:
		pin.off()
	else:
		pin.on()
	print(pin, pin.value())

tm = TimerManager()

if isIrigatie:
	durationAspersoare = 15
	durationPicurator = 20
	c = tm.add(TimerConfig("Rotoare ON", lambda: (setEnableTimeSync(False), pinRotoare.on()), 5, 0))
	c = tm.add(TimerConfig.createWithOffset(c, "Rotoare OFF", lambda: pinRotoare.off(), durationAspersoare))

	c = tm.add(TimerConfig.createWithOffset(c, "Picurator ON", lambda: pinPicurator.on(), 0))
	c = tm.add(TimerConfig.createWithOffset(c, "Picurator OFF", lambda: pinPicurator.off(), durationPicurator))

	c = tm.add(TimerConfig.createWithOffset(c, "Foisor + Strada ON", lambda: (pinFoisor.on(), pinStrada.on()), 0))
	c = tm.add(TimerConfig.createWithOffset(c, "Foisor + Strada OFF", lambda: (pinFoisor.off(), pinStrada.off(), setEnableTimeSync(True)), durationAspersoare))
else:
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
		str = calculateValveState()
		pinRobinet.off() # start moving
		log("Valve started moving with state: " + str)
		valveSecurityTimer.init(period=30 * 1000, mode=machine.Timer.ONE_SHOT, callback=lambda t: (pinRobinet.on(), log("Valve error")))
		
	def handleValveOpenOrClose():
		if (valveState == 0
				or valveState == 1 and pinRobinetClosed.value() == 0
				or valveState == 2 and pinRobinetOpen.value() == 0):
			pinRobinet.on()
			valveSecurityTimer.deinit()
			log("Valve stopped moving with state: " + calculateValveState())

	from debouncer import Debouncer
			
	d1 = Debouncer(pinRobinetButon, startValveMotor)
	d2 = Debouncer(pinRobinetOpen, handleValveOpenOrClose)
	d3 = Debouncer(pinRobinetClosed, handleValveOpenOrClose)

timeSync = TimeSync(timeZoneOffsetSec = 3 * 3600)

def defineBlynkHandlers():
	@blynk.on("connected")
	def blynkConnected(ping):
		log('Blynk ready. Ping: ' + str(ping) + 'ms')

	@blynk.on("disconnected")
	def blynkDisconnected():
		log('Blynk disconnected')
		
	@blynk.VIRTUAL_READ(0)
	def getStatus():
		now = utime.localtime()
		str = "{:02d}:{:02d}:{:02d} rot{}, pic{}, foi{}, str{}".format(now[3], now[4], now[5], pinRotoare.value(), pinPicurator.value(), pinFoisor.value(), pinStrada.value())
		blynk.virtual_write(0, str)
	
	@blynk.VIRTUAL_WRITE(1)
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
		tm.run()
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
	