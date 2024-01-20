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
USE_BLINK = True
# USE_BLINK = False

print("Memory at boot:", gc.mem_free());

# import it here, because in the other files we get memory allocation error. Maybe a lot
# of mem is already used because of the big string of the script
if USE_BLINK:	
	import BlynkLib
	gc.collect();

# v1 of "hot reload"
# with open("program.py") as f:
	# exec(f.read(), globals());

# v2 of "hot reload". Cf. README.md, it worked more or less well in 2019. But in 2022, I didn't
# feel the need to use it. And importing directly, cf. below, has the advantage of having the import
# already imported in REPL. So things from e.g. program.pinRobinetOpen can be accessed directly.
# memory: direct import, free mem = 18944; ru: 18512
# import reloadutil as ru;
# # TODO: when adding "definitions", there is somehow a memory leak; only 2 or 3 reloads are possible
# ru.moduleNames = ["program"];
# ru.reload(globals());

import program
import debouncer

gc.collect();
print("Memory after importing program: " + str(gc.mem_free()));