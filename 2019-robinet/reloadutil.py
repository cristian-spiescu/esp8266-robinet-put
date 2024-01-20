import sys
import gc

# usage: func = reload(func)
def reloadOne(mod):
    mod_name = mod.__name__
    del sys.modules[mod_name]
    return __import__(mod_name)

moduleNames = []

def callUnload():
	for moduleName in moduleNames:
		if not moduleName in sys.modules:
			continue;
		m = sys.modules[moduleName];
		if hasattr(m, "onUnloadModule"):
			m.onUnloadModule()
	
	
def reload(globals = None):
	gc.collect();
	callUnload();
	for moduleName in moduleNames:
		if globals and moduleName in globals:
			del globals[moduleName]
		if not moduleName in sys.modules:
			continue;
		del sys.modules[moduleName];
	for moduleName in moduleNames:
		# gc.collect();
		# print(gc.mem_free(), moduleName);
		__import__(moduleName);
	