import machine
import micropython

class Debouncer:
	def __init__(self, pin, cb, irqMode = machine.Pin.IRQ_FALLING, wantedValue = 0, period = 100):
		self.pin = pin
		self.cb = cb
		self.wantedValue = wantedValue
		self.period = period
		self.justCalled = False
		self.timer = machine.Timer(-1)
		pin.irq(self.irqHandler, irqMode)
		
		self.ccb = self.timerHandler;
	
	def irqHandler(self, pin):
		if self.justCalled:
			return;
		else:
			self.justCalled = True
			# print("handler")
			# micropython.schedule(Debouncer.sch, self)
			self.timer.init(period=self.period, mode=machine.Timer.ONE_SHOT, callback=self.ccb);
	
	def timerHandler(self, t):
		# print("tim", self.pin.value())
		self.justCalled = False
		if self.pin.value() == self.wantedValue:
			self.cb()
			# micropython.schedule(Debouncer.sch, self)
			
	def sch(self):
		self.justCalled = False
		self.timer.init(period=self.period, mode=machine.Timer.ONE_SHOT, callback=self.timerHandler)
		# self.cb();