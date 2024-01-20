import machine
import utime
import ntptime
from logger import log
import definitions as df;
	
class TimeSync:
	
	def __init__(self, timeZoneOffsetSec = 0, intervalSec = 3600, errorIntervalSec = 60):
		self.timeZoneOffsetSec = timeZoneOffsetSec;
		self.intervalSec = intervalSec;
		self.errorIntervalSec = errorIntervalSec;
		self.lastSync = None;
		self.error = False;
	
	def syncIfNeeded(self):
		if not df.firstConnectionSucceded:
			return; # w/o this, at boot we'd have an error, because the Wifi is not yet UP
		now = utime.time()
		if (not self.lastSync # first run
				or now < self.lastSync # clock overrun
				or now - self.lastSync > self.intervalSec # interval has passed
				or self.error and now - self.lastSync > self.errorIntervalSec): # we had recently a sync error, and the interval for the error case has passed
			self.sync(now);
			self.lastSync = utime.time();
	
	def sync(self, before):
		try:
			if not df.wlan.isconnected():
				raise Exception()
			ntptime.settime()
			# content = seconds
			after = utime.time()
			after += self.timeZoneOffsetSec;
			
			# content = tuple of 8
			tm = utime.localtime(after)
			# again a tuple of 8; but rearranged; cf. ntptime.py; I didn't find official doc
			tm = tm[0:3] + (0,) + tm[3:6] + (0,)
			# set the time
			machine.RTC().datetime(tm)
			
			log("NTP time sync OK; drift = " + str(after - before) + "s")
			self.error = False;
		except:
			log("NTP time sync ERROR");
			self.error = True;
