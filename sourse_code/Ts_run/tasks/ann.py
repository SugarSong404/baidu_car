import time
from tasks.utils import *
def ann_task(tsks, has_enter = False):
    ann_f = 0
    dev = 0
    dev_y = 0
    if has_enter:print("前任务判进圆环")
    else:
        lane_until_det(tsks.car, tsks.det_tree, tsks.lane, 2, 0.55, 0, scale = 350, timeout = 20)
    while True:
        img = tsks.car.cap_front.read()
        if img is None: continue
        res = tsks.det_tree.predict_area(img)
        if (len(res)!=0 and res[0][0]==2):
            if ann_f == 0:
                print(f"检测到{'出' if has_enter else '入'}环标志")
                wait_time = time.time()
                ann_f = 1 
            elif ann_f==2:
                print("检测到出环标志")
                wait_time = time.time()
                ann_f = 3
        elif ann_f==1 and time.time() - wait_time > 2.5:
            if has_enter:break
            ann_f = 2
        elif ann_f==3 and time.time() - wait_time > 2: break

        if has_enter or (not has_enter and ann_f >= 1):
            dev = tsks.lane2.predict(img)/310
        else:
            dev = tsks.lane.predict(img)/330

        if (not has_enter) and (ann_f==1):dev_y = 0.001
        y_speed = tsks.car.pid_lane_y(dev_y)
        angle_speed = tsks.car.pid_lane(dev)
        tsks.car.set_velocity(0.55, y_speed, angle_speed)


