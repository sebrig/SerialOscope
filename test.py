import schedule
import time

def ma_fonction():
    print("appelée !")

schedule.every(0.25).seconds.do(ma_fonction)

while True:
    schedule.run_pending()
    print("loop")
    #time.sleep(0.1)