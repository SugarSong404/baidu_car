import threading, time
from tasks.utils import *

def find_cylinder_pose(car, det_hanota, direction):
    cylinders = []
    dis = []
    while len(cylinders) < 3:
        while True:
            img = car.cap_side.read()
            if img is None: continue
            car.set_velocity(0.2, 0, 0)
            det_res = det_hanota.predict(img)
            if det_res is not None:
                boxes = det_res.get('boxes', None)
                if boxes is None or len(boxes)==0:continue
                else:
                    f = False
                    for box in boxes:
                        if not int(box[0]) in cylinders and int(box[0]) < 3:
                            cylinders.append(int(box[0]))
                            f = True
                            break
                    if f:break
        align_det(car, det_hanota, cylinders[-1], 10, drct = direction)
        dis.append(list(car.chassis.odom.pose)[0])
    return [dis[cylinders.index(0)], dis[cylinders.index(1)], dis[cylinders.index(2)], dis[2] + 0.128]


def do_hanota(id, car, direction, dis):
    print(f"正在对齐圆柱（{2-id}）")
    car.move_from_zero(dis[2-id], 0.2, 0)
    if direction==1:pose1=0.04
    elif direction==-1:pose1=0.26
    if id==0:
        car.task.arm.set(0.15,0.094)
        car.task.arm.set(pose1,0.094)
    car.task.arm.set_hand_angle(19)
    #time.sleep(0.2)
    print(f"正在拿取圆柱（{2-id}）")
    car.task.my_pick_up_cylinder(id, direction)
    print(f"正在返回终点（{2-id}）")
    car.move_from_zero(dis[3], 0.2, 0)
    print(f"正在放下圆柱（{2-id}）")
    car.task.my_put_down_cylinder(id, direction)
    if id==2:
        #car.task.arm.set_hand_angle(-25)
        car.move_dis_precise(direction*0.027, 0.05 , 1)
        car.task.arm.set_offset(direction*0.05,0)
        #time.sleep(0.5)
        #car.task.arm.set_hand_angle(15)
    time.sleep(0.1)

def true_fork_task(car, lane, det_arrow):
    car.move_dis_precise(0.75, 0.5, 0)
    print("正在判断箭头方向")
    while True:
        img = car.cap_front.read()
        if img is None:continue
        res= det_arrow.predict_area(img)
        if len(res)!=0:
            direction = 1 if res[0][0]==0 else -1
            break
    print("正在转向前进")
    threading.Thread(target=lambda: (car.task.arm.switch_side(-1*direction)), daemon=True).start()
    car.move_from_zero(0.3*direction, 0.3 , 2)
    lane_until_dis(car, lane, 0.53, 0.5, 350)
    lane_until_time(car, lane, 0, 1.5, 0.8, scale = 350)
    car.move_dis_precise(-direction*0.027, 0.05 , 1)
    return direction


def true_hanota_task(car, det_hanota, direction):
    try:
        dis = find_cylinder_pose(car, det_hanota, direction)
        for i in range(3):do_hanota(i, car, direction, dis)
        car.task.arm.switch_side(1)
        threading.Thread(target=lambda: (car.task.arm.set(0.15, 0.015)), daemon=True).start()
        time.sleep(0.5)
        car.move_dis_precise(-0.15*direction, 0.2 , 2)
    except Exception as e:
        car.task.arm.set(0.15, 0.015)
        car.task.arm.switch_side(1)
        print(f"运行错误：{e}")


def hanota_task(tsks, direction):
    true_hanota_task(tsks.car, tsks.det_hanota, direction)

def fork_task(tsks):
    return true_fork_task(tsks.car, tsks.lane, tsks.det_arrow)


