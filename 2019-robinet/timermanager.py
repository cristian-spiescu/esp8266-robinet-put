import utime
from logger import log, debug, D_TMGR
	
class TimerConfig:
	
	def __init__(self, name, runnable, hour, minute, dayOfWeek = None):
		self.name = name;
		self.runnable = runnable;
		self.hour = hour;
		self.minute = minute;
		# None, or 0..6; maybe in the future we add e.g. [1, 2, 4, 5]
		self.dayOfWeek = dayOfWeek;
	
	@staticmethod
	def createWithOffset(referenceConfig, name, runnable, offsetMin, dayOfWeek = None):
		minute = referenceConfig.minute + offsetMin;
		hour = (referenceConfig.hour + int(minute / 60)) % 24;
		minute = minute % 60;
		return TimerConfig(name, runnable, hour, minute, dayOfWeek);
	
	def __str__(self):
		return "TC[name = {}, dow = {}, time = {:02d}:{:02d}]".format(self.name, self.dayOfWeek, self.hour, self.minute);

# TODO: a theoretical issue: a timer for 10:15. At 10:14:59 the NTP updates the clock. There is a big drift => now is 10:16:01
# however this means that the drift > 60s. With the current hourly NTP sync, I don't think I've spotted drifts that high.
class TimerManager:
	
	def __init__(self):
		self.configs = [];
		self.lastRun = (-1, -1);

	def add(self, config):
		self.configs.append(config);
		return config;

	def run(self):
		self.runInternal(utime.localtime());
	
	def runInternal(self, now):
		nowHour = now[3];
		nowMinute = now[4];
		nowDayOfWeek = now[6];
		
		if (self.lastRun == (nowHour, nowMinute)):
			# did run this minute
			return;
		self.lastRun = (nowHour, nowMinute);
		
		debug(D_TMGR, "TimerManager.run() at", now);

		for config in self.configs:
			debug(D_TMGR, "Processing config", config);
			if (config.dayOfWeek # if specified
					and config.dayOfWeek != nowDayOfWeek): # and no match
				debug(D_TMGR, "Skipping because no day match");
				continue; # skip config
			# else either dayOfWeek unspecified or we have a match
			if nowHour != config.hour or nowMinute != config.minute:
				debug(D_TMGR, "Skipping because no hour/min match");
				continue;
			# else we have a match on hours
			config.dayOfWeekRan = nowDayOfWeek; # quickly set this; so next run/second it will skif cf. "if" above
			log("Running TimerConfig = " + config.name);
			config.runnable();