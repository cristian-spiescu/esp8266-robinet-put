from machine import Pin, Timer
from time import sleep
from micropython import schedule

print("main.py")

# D4
pinLed = Pin(2, Pin.OUT)

def mainInfiniteLoop():
    while True:
        pinLed.value(not pinLed.value())
        sleep(1)

blinkTimer = Timer(-1)
def start():
    period = 500
    blinkTimer.init(period=period, mode=Timer.PERIODIC, callback=blinkTimerHandler)

def blinkTimerHandler(timer):
    schedule(blink, 0)

def blink(dummy):
    pinLed.value(not pinLed.value())
    print("countIrq", countIrq, "timerStarts", timerStarts, "timerFinishes", timerFinishes)

countIrq = 0
timer = Timer(-1)
timerOn = False
timerStarts = 0
timerFinishes = 0

def irqHandler(pin):
    global countIrq, timerOn
    countIrq = countIrq + 1
    if not timerOn:
        # schedule(irqHandler2, 0)
        pinRobinetButon.irq(trigger=0)
        timerOn = True

# def irqHandler2(dummy):
        global timerStarts
        timerStarts += 1
        timer.init(mode=Timer.ONE_SHOT, period=100, callback=timerHandler)

def timerHandler(timer):
    global timerOn, timerFinishes
    timerFinishes += 1
    timerOn = False
    pinRobinetButon.irq(irqHandler, Pin.IRQ_FALLING)

# D7
pinRobinetButon = Pin(13, Pin.IN, Pin.PULL_UP)
pinRobinetButon.irq(irqHandler, Pin.IRQ_FALLING)

# start()
