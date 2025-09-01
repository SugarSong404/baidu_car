import time
import threading
from tasks.utils import *

def bag_task(tsks, order = 0, other_f = True):
    try:
        print("确认发射点中")
        lane_until_det(tsks.car, tsks.det_bag, tsks.lane, 0, 0.5, scale = (320 if order==1 else 280), frames = 1, timeout = 20)
        lane_until_time(tsks.car, tsks.lane, 0.3, 3, dev_tho = 1.5, scale = 350)
        align_det(tsks.car, tsks.det_bag, 0, 10, drct = -1, pid_big = True, center = (380 if order==0 else 420))
        if order==0:
            tsks.car.chassis.odom.reset()
            tsks.car.move_from_zero(-0.05, 0.1, 0)
        tsks.car.task.my_send2(order + 1)
        if order == 0 and not other_f:lane_not_det(tsks.car, tsks.det_bag, tsks.lane, 0, 0.55, scale = 350, frames = 3)
        print("正在发射沙包")
        return True
    except Exception as e:
        print(f"运行错误：{e}")
        return False
