from machine import RTC

rtc = RTC()

def log(string):
        t = rtc.datetime()
        st = str(t[0]) + "-" + str(t[1]) + "-" + str(t[2]) + " " + str(t[4]) + ":" + str(t[5]) + ":" + str(t[6])
        print("[UTC] " + st + " " + string)