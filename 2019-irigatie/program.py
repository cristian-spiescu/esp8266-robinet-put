from timermanager import TimerManager, TimerConfig;
import definitions as df;
from logger import log;
from timesync import TimeSync;
import machine;
from machine import Timer;
import utime;
import gc;

def onUnloadModule():
	timer.deinit();

log("Starting program");

import __main__;
USE_BLINK = __main__.USE_BLINK;
BLYNK_RETRY_INTERVAL_SEC = 60;

# @see TimerManager. The current implementation needs that this is less then 1 min. However, I don't
# see why this should be bigger than 1 / a few secs
LOOP_TIMER_PERIOD_SEC = 1;
# USE_BLINK is in boot.py

with open("wifi_cfg.py") as f:
    exec(f.read(), globals())

enableTimeSync = True

def setEnableTimeSync(value):
	global enableTimeSync;
	enableTimeSync = value;

pinRotoare = machine.Pin(16, machine.Pin.OUT)
pinRotoare.value(0);
pinPicurator = machine.Pin(5, machine.Pin.OUT)
pinPicurator.value(0);
pinFoisor = machine.Pin(4, machine.Pin.OUT)
pinFoisor.value(0);
pinStrada = machine.Pin(14, machine.Pin.OUT)
pinStrada.value(0);
dictPins = { "rot": pinRotoare, "pic": pinPicurator, "foi": pinFoisor, "str": pinStrada }

durationAspersoare = 15;
durationPicurator = 20;

tm = TimerManager()
c = tm.add(TimerConfig("Rotoare ON", lambda: (setEnableTimeSync(False), pinRotoare.on()), 5, 0));
c = tm.add(TimerConfig.createWithOffset(c, "Rotoare OFF", lambda: pinRotoare.off(), durationAspersoare));

c = tm.add(TimerConfig.createWithOffset(c, "Picurator ON", lambda: pinPicurator.on(), 0));
c = tm.add(TimerConfig.createWithOffset(c, "Picurator OFF", lambda: pinPicurator.off(), durationPicurator));

c = tm.add(TimerConfig.createWithOffset(c, "Foisor + Strada ON", lambda: (pinFoisor.on(), pinStrada.on()), 0));
c = tm.add(TimerConfig.createWithOffset(c, "Foisor + Strada OFF", lambda: (pinFoisor.off(), pinStrada.off(), setEnableTimeSync(True)), durationAspersoare));

timeSync = TimeSync(timeZoneOffsetSec = 3 * 3600);

def defineBlynkHandlers():
	@blynk.on("connected")
	def blynkConnected(ping):
		log('Blynk ready. Ping: ' + str(ping) + 'ms');

	@blynk.on("disconnected")
	def blynkDisconnected():
		log('Blynk disconnected');
		
	@blynk.VIRTUAL_READ(0)
	def getStatus():
		now = utime.localtime();
		str = "{:02d}:{:02d}:{:02d} rot{}, pic{}, foi{}, str{}".format(now[3], now[4], now[5], pinRotoare.value(), pinPicurator.value(), pinFoisor.value(), pinStrada.value());
		blynk.virtual_write(0, str);
	
	@blynk.VIRTUAL_WRITE(1)
	def execBlynkCommand(value):
		spl = value[0].split(" ");
		log("Exec blynk cmd {}".format(str(spl)));
		result = "Unknown command"
		c = spl[0]
		if c == "help":
			result = "Available commands: help, mem, " + ", ".join(dictPins.keys())
		elif c == "mem":
			beforeC = gc.mem_free()
			gc.collect();
			result = "Free mem (before / after GC): {} / {}".format(beforeC, gc.mem_free());
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
			timeSync.syncIfNeeded();	
		tm.run();
		if USE_BLINK and df.wlan.isconnected():
			import BlynkLib; # was already imported in boot.py
			global blynk;
			global lastConnectAttempt;
			if not blynk:
				blynk = BlynkLib.Blynk(BLYNK_AUTH);
				defineBlynkHandlers();
			elif (blynk.state == BlynkLib.DISCONNECTED # may be CONNECTING, so this check is needed
					and utime.time() - lastConnectAttempt > BLYNK_RETRY_INTERVAL_SEC):
				lastConnectAttempt = utime.time();
				blynk.connect();
			blynk.run();
	finally:
		timer.init(period=LOOP_TIMER_PERIOD_SEC * 1000, mode=Timer.ONE_SHOT, callback=lambda t:loop());		
	
df.do_connect(WIFI_CONFIG[0], WIFI_CONFIG[1]);
df.blink();

timer = Timer(-1);
loop();

#print("Starting Blynk");
#while True:
#	blynk.run()
#	machine.idle()
	