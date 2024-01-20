import machine
import micropython

# When enabled, this may trigger a lot pollution to the console, which would prevent uPyLoader to transfer files
# That's why it's enable-able (via REPL), being disabled by default.
DEBUG_DEBOUNCER = False

# If a lot of events occur, the in irqHandler(), although the timer is scheduled, the callback is not
# called. I interpret this: the IRQ queue (if such a thing exists) is full, and when the timer wants
# to queue the handler, it doesn't have any room. And it doesn't retry or so. 
# Cf. here https://selfhostedhome.com/debouncing-buttons-in-micropython/, I stopped the IRQ during the timer
# The methods have several "print"; the last ones are commented. I was suspecting that an interrupt
# is triggered when a interrupt handler is in progress. But this doesn't seem to be the case
class Debouncer:
	def __init__(self, pin, cb, irqMode = machine.Pin.IRQ_FALLING, wantedValue = 0, period = 100):
		self.pin = pin
		self.cb = cb
		self.wantedValue = wantedValue
		self.period = period
		self.justCalled = False
		self.timer = machine.Timer(-1)
		pin.irq(self.irqHandler, irqMode)
		
		# seems that this is the equivalent of JS bind(), which means mem allocation, hence not allowed
		# in ISR; cf. https://docs.micropython.org/en/latest/reference/isr_rules.html#creation-of-python-objects
		self.ccb = self.timerHandler;
		# if this really means mem alloc, then I put this; because used in timerHandler, which is an interrupt
		# handler as well
		self._irqHandler = self.irqHandler;
	
	def irqHandler(self, pin):
		if self.justCalled:
			logDebouncer("Debouncer.irqHandler 1 " + str(pin))
		else:
			logDebouncer("Debouncer.irqHandler 2 " + str(pin))
			self.justCalled = True
			# even if I disable the IRQ, after this, a few more calls happen (falling into the above if branch)
			# I interpret this as these calls being queued
			pin.irq(trigger=0);
			self.timer.init(period=self.period, mode=machine.Timer.ONE_SHOT, callback=self.ccb);
			# I don't really think it's needed; I was experimenting. But
			# this told me almost everytime: RuntimeError: schedule queue full
			# micropython.schedule(self.ccb1, 0);
			# logDebouncer("Debouncer.irqHandler 2.1 " + str(pin))
		# logDebouncer("Debouncer.irqHandler 3 " + str(pin))

	def timerHandler(self, t):
		logDebouncer("Debouncer.timerHandler " + str(self.pin) + " final value = " + str(self.pin.value()))
		self.justCalled = False
		# logDebouncer("Debouncer.timerHandler 2")
		if self.pin.value() == self.wantedValue:
			# self.cb()
			micropython.schedule(callCallback, self)
		self.pin.irq(self._irqHandler, machine.Pin.IRQ_FALLING)
		# logDebouncer("Debouncer.timerHandler 3")

def callCallback(debouncer):
	debouncer.cb();

def logDebouncer(str):
	if DEBUG_DEBOUNCER:
		print(str)