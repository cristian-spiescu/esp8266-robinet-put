import time

class PollingPin:
    def __init__(self, pin, cb, wantedValue = 0, waitPeriod = 100):
        self.pin = pin
        self.cb = cb
        self.wantedValue = wantedValue
        self.waitPeriod = waitPeriod
        self.previousValueStable = None
        self.previousValue = None
        self.previousValueTimestamp = None
        self.enabled = False
    
    def enable(self):
        self.enabled = True
        self.previousValueStable = self.previousValue = self.previousValueTimestamp = None
    
    def disable(self):
        self.enabled = False

    def run(self):
        if not self.enabled:
            return
        newValue = self.pin.value()
        if self.previousValueTimestamp == None or newValue != self.previousValue:
            self.previousValue = newValue
            self.previousValueTimestamp = time.ticks_ms()
        elif time.ticks_ms() - self.previousValueTimestamp > self.waitPeriod:
            if self.previousValueStable != newValue:
                self.previousValueStable = newValue
                if newValue == self.wantedValue:
                    self.cb()


    