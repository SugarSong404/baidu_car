import time
import threading
from tasks.utils import *

def final_task(tsks, only_lane = False):
    car = tsks.car
    det_final = tsks.det_final
    lane = tsks.lane

    car.task.arm.switch_side(1)
    threading.Thread(target=lambda: (car.task.arm.set(0.15, 0.07)), daemon=True).start()
    print("正在寻找终点位置")
    lane_until_precise(car, det_final, lane, 0.55, dis_tho = [0, 350], area_tho = [0, 100000], timeout = (40 if only_lane else 20), scale = 240)
    forward_until_precise(car, det_final, 0.2, dis_tho = [0, 250], area_tho = [0, 100000])
    car.set_velocity(0, 0, 0)
    car.chassis.odom.reset()

    print("正在撞击老人")
    car.move_from_zero(0.3,0.45,0)
    #time.sleep(0.1)
    car.task.arm.set(0.28, 0.04,speed=[0.18,0.1])
    
    car.move_from_zero(0.1,0.45,1)
    time.sleep(0.1)
    
    car.move_from_zero(-0.05,0.45,0)
    time.sleep(0.1)

    car.move_from_zero(0.35,0.45,1)
    time.sleep(0.1)
    
    car.move_from_zero(0.01,0.45,1)
    time.sleep(0.1)
    
    print("正在入库")
    car.move_from_zero(0.72,0.55,0)


