# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
import uos, machine
#uos.dupterm(None, 1) # disable REPL on UART(0)
import gc
import webrepl
webrepl.start()
gc.collect()

# maybe we want to disable Blynk; during tests I saw cases with some strange behavior,
# including ESP reset. 
USE_BLINK = True;

print("Memory at boot:", gc.mem_free());

# import it here, because in the other files we get memory allocation error. Maybe a lot
# of mem is already used because of the big string of the script
if USE_BLINK:	
	import BlynkLib
	gc.collect();

import reloadutil as ru;
# TODO: when adding "definitions", there is somehow a memory leak; only 2 or 3 reloads are possible
ru.moduleNames = ["timermanager", "timesync", "program"];
ru.reload(globals());
	
# with open("program.py") as f:
	# exec(f.read(), globals());

from logger import log;
gc.collect();
log("Memory after importing program: " + str(gc.mem_free()));


		
