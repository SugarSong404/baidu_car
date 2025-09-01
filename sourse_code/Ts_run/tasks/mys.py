from tasks.utils import *
import time, threading


def lane_id_det_precise(car, det, lane, id, sp=0.3, scale = 500, timeout=5, end = 0, precise = 0):
    t = time.time()
    while True:
        if time.time() - t > timeout: raise TimeoutError("lane_id_det 超时")
        img = car.cap_side.read()
        if img is None: continue
        img2 = car.cap_front.read()
        if img2 is None: continue

        dev = lane.predict(img2)/scale
        angle_speed = car.pid_lane(dev)
        car.set_velocity(sp, 0, angle_speed)
        det_res = det.predict(img)
        if det_res is not None:
            boxes = det_res.get('boxes', None)
            if boxes is None or len(boxes)==0:
                continue
            else:
                for res in det_res['boxes']:
                    if int(res[0])==id and res[1] > precise and res[3] < end:return

def mys_task(tsks):
    car = tsks.car
    det = tsks.det_mys
    lane = tsks.lane
    try:
        print("正在寻找位置")
        lane_id_det_precise(car, det, lane, 0, sp=0.55, scale = 350, timeout=10, end = 300, precise=0.9)
        car.chassis.odom.reset()
        print("正在对齐目标")
        align_det(car, det, 0, 10, drct=-1, frames=2)
        car.chassis.odom.reset()
        car.move([-0.01, 0.03, -0.025], [0.05, 0.05, 0.05])
        print("正在执行夹取物块")
        car.task.mysterious_mission()
        time.sleep(1.5)
        car.task.arm.switch_side(1)
        threading.Thread(target=lambda: (car.task.arm.set(0.15, 0.015)), daemon=True).start()
        car.move_dis_precise(-0.03, 0.05, 1)
    except Exception as e:
        tsks.car.task.arm.set(0.15, 0.05)
        print(f"运行错误：{e}")
