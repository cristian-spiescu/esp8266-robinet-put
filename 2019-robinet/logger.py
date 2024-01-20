import os
import utime
import machine

D_LOGGER = 0;
D_TMGR = 1;
D_COUNT = 2;
DEBUG_ENABLED = [False] * D_COUNT;

def debug(who, *args):
	global DEBUG_ENABLED;
	if DEBUG_ENABLED[who]:
		print(*args)

class Logger:
	
	def __init__(self):
		self.file = "log";
		self.maxLines = 100;
		self.currentLines = 0;
		self.maxFiles = 3; # e.g. for 10: log.0 ... log.9
		self.lastDate = None
	
	def log(self, str):
		# preppend time
		d = utime.localtime();
		str = "{:02d}:{:02d}:{:02d} {}".format(d[3], d[4], d[5], str);
		
		# print the date part only when it changes
		date = (d[0], d[1], d[2])
		if (self.lastDate != date):
			self.lastDate = date;
			str = "## {:04d}-{:02d}-{:02d}\n{}".format(d[0], d[1], d[2], str)
		
		# print the string in console and in file
		print(str)
		try:
			s = machine.disable_irq()
			with open(self.file + ".0", "a+") as f:
				f.write(str)
				f.write("\n")
		finally:
			machine.enable_irq(s)
		
		self.currentLines += 1;	
		if (self.currentLines > self.maxLines):
			self.rotate();
			self.currentLines = 0;
			
	def rotate(self):
		for i in range(self.maxFiles - 1, -1, -1): # .0 is the last one
			current = self.file + "." + str(i);
			if i == self.maxFiles - 1:
				try:
					debug(D_LOGGER, "Removing file:", current);
					os.remove(current);
					debug(D_LOGGER, "OK");
				except:
					debug(D_LOGGER, "FAIL");
					pass
			else:
				older = self.file + "." + str(i + 1);
				try:
					debug(D_LOGGER, "Renaming:", current, "to:", older);
					os.rename(current, older);
					debug(D_LOGGER, "OK");
				except: 
					debug(D_LOGGER, "FAIL");		
		
def log(str):
	logger.log(str)

logger = Logger();
