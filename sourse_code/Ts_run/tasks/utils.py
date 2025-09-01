import numpy as np
import cv2, time, os

def mask_img(img, region1):
    region = region1.copy()
    region[0] = max(0, region[0]-40)
    region[2] = min(639, region[2]+40)
    region[1] = max(0, region[1]-40)
    region[3] = min(479, region[3]+40)
    masked_img = np.zeros_like(img)
    cropped_region = img[int(region[1]):int(region[3]), int(region[0]):int(region[2]),:]
    masked_img[int(region[1]):int(region[3]), int(region[0]):int(region[2]),:] = cropped_region
    return masked_img

def timed_call(func, *args, **kwargs):
    name = func.__name__
    print(f"\n----------- 任务 {name} 正在开始执行 -----------")
    start = time.time()
    result = func(*args, **kwargs)
    duration = time.time() - start
    print(f"----------- 执行完毕，耗时 {duration:.3f}---------\n")
    return result

def align_det(car, det, id, tho, drct=1, region=None, timeout=5, frames = 1, pid_big = False, center = 320):
    t_start = time.time()
    nums = 0
    pid = car.pid_align_bag if pid_big else car.pid_align
    while True:
        if time.time() - t_start > timeout:
            raise TimeoutError("align_det 超时")
        img = car.cap_side.read()
        if img is None:continue 
        if region is not None:img = mask_img(img, region)
        det_res = det.predict(img)
        if det_res is None or 'boxes' not in det_res or len(det_res['boxes']) == 0:
            car.set_velocity(0.1, 0, 0)
            continue
        index = -1
        for i, box in enumerate(det_res['boxes']):
            if int(box[0]) == id:
                index = i
                break
        if index == -1:
            car.set_velocity(0, 0, 0)
            continue
        box = det_res['boxes'][index]
        dis = ((box[2] + box[4]) / 2) - center
        if abs(dis) < tho:nums+=1
        if nums > frames:break
        pid_output = pid(dis)
        car.set_velocity(pid_output*drct, 0, 0) 
    car.set_velocity(0, 0, 0)

def cal_area(box_arr):
    w = abs(box_arr[0]-box_arr[2])
    h = abs(box_arr[1]-box_arr[3])
    return w*h

def align_end(car, det, id, tho, drct=1, region=None, timeout=5, frames=3):
    t_start = time.time()
    consecutive = 0
    pid = car.pid_align_end

    while True:
        if time.time() - t_start > timeout:
            print("align_end 超时")
            break
        img = car.cap_side.read()
        if img is None:continue
        if region is not None:img = mask_img(img, region)
        
        det_res = det.predict(img)
        if det_res is None or 'boxes' not in det_res or len(det_res['boxes']) == 0:
            car.set_velocity(0.1, 0, 0)
            continue
        
        index = -1
        for i, box in enumerate(det_res['boxes']):
            if int(box[0]) == id:
                index = i
                break
        if index == -1:
            car.set_velocity(0, 0, 0)
            continue
        
        box = det_res['boxes'][index]
        print("---------------------------")
        print(cal_area(box[2:]))
        dis = box[5]
        print(dis)
        
        if abs(dis - tho) < 5:consecutive += 1
        else:consecutive = 0
        
        if consecutive >= frames:break
        pid_output = pid(dis - tho)
        car.set_velocity(0, -pid_output * drct, 0)
    car.set_velocity(0, 0, 0)



def check_det(car, det, id, frames = 5):
    times = 0
    while times < frames:
        times += 1
        img = car.cap_side.read()
        if img is None:continue 
        det_res = det.predict(img)
        if det_res is None or 'boxes' not in det_res or len(det_res['boxes']) == 0:continue
        for _, box in enumerate(det_res['boxes']):
            if int(box[0]) == id:
                return True
    return False


def align_ocr(car, ocr, tho, drct = 1 ,region = None, sp = 0.05, timeout=5):
    last_res = 0
    d = 1
    t = time.time()
    while(True):
        if time.time() - t > timeout: raise TimeoutError("align_ocr 超时")
        img = car.cap_side.read()
        if img is None: continue
        if region is not None: img = mask_img(img, region)
        res = ocr.predict_center(img, tho)
        if last_res == 2 and res == 2: break
        last_res = res
        if abs(res) == 1: d = res * drct
        car.set_velocity(d * sp, 0, 0)
    car.set_velocity(0, 0, 0)

def rec_ocr(car, ocr, pre = 0.9 ,region = None, timeout=0.5):
    timeout = 0.5
    text = ""
    t = time.time()
    while True:
        if time.time() - t > timeout: return "这是一段未识别成功的文本，但请你还是要按照要求随便做出一个回答"
        img = car.cap_side.read()
        if img is None: continue
        if region is not None: img = mask_img(img, region)
        res = ocr.predict_lines(img, pre)
        if len(res)==0: continue
        for i in range(len(res)):
            text += res[i]
        break
    return text

def rec_ocr_multi(car, ocr, pre = 0.9 ,region = None, num = 1, timeout=0.5, exit_f = True):
    timeout = 0.5
    t = time.time()
    while True:
        if time.time() - t > timeout: 
            if exit_f:raise TimeoutError("rec_ocr_multi 超时")
            else:return ["你猜","你再猜","你再猜猜","你再猜猜猜"]
        img = car.cap_side.read()
        if img is None: continue
        if region is not None: img = mask_img(img, region)
        res = ocr.predict_lines(img, pre)
        if len(res) < num: continue
        return res

def chat_answer(chat, problem, timeout=15):
    ans = ""
    t = time.time()
    while True:
        if time.time() - t > timeout: raise TimeoutError("chat_answer 超时")
        ans = chat.predict(problem)
        if ans == "ER": continue
        break
    return ans

def forward_until_precise(car, det, sp, ids = [0], pre = 0.9, dis_tho = [0, float('inf')], area_tho = [0, float('inf')], timeout=5):
    t = time.time()
    while True:
        if time.time() - t > timeout: raise TimeoutError("forward_until_precise 超时")
        img = car.cap_front.read()
        if img is None: continue
        result = det.predict_precise(img, ids, pre, dis_tho, area_tho)
        if result: break
        car.set_velocity(sp, 0, 0)

def forward_until_det(car, det, id = 0, sp=0.2, reverse = False, frames = 5, timeout=5):
    object_times = 0
    n_object_times = 0
    t = time.time()
    while True:
        if time.time() - t > timeout: raise TimeoutError("forward_until_det 超时")
        img = car.cap_side.read()
        if img is None: continue
        car.set_velocity(sp, 0, 0)

        det_res = det.predict(img)
        if det_res is not None:
            boxes = det_res.get('boxes', None)
            if boxes is None or len(boxes)==0:
                if reverse: break
            else:
                object_f = any(int(box[0]) == id for box in det_res['boxes'])
                if object_f:
                    object_times += 1
                    n_object_times = 0
                else:
                    object_times = 0
                    n_object_times += 1
        if not reverse and object_times > frames: break
        elif reverse and n_object_times > frames: break

def lane_until_det(car, det, lane, id = 0, sp=0.3, cap = 1, reverse = False, y_dev = 0, frames = 5, scale = 500, timeout=5):
    object_times = 0
    n_object_times = 0
    t = time.time()
    while True:
        if time.time() - t > timeout: raise TimeoutError("lane_until_det 超时")
        img = car.cap_side.read()
        if img is None: continue
        img2 = car.cap_front.read()
        if img2 is None: continue

        dev = lane.predict(img2)/scale
        y_speed = car.pid_lane_y(y_dev)
        angle_speed = car.pid_lane(dev)
        car.set_velocity(sp, y_speed, angle_speed)

        img = img2 if cap==0 else img

        det_res = det.predict(img)
        if det_res is not None:
            boxes = det_res.get('boxes', None)
            if boxes is None or len(boxes)==0:
                if reverse: break
            else:
                object_f = any(int(box[0]) == id for box in det_res['boxes'])
                if object_f:
                    object_times += 1
                    n_object_times = 0
                else:
                    object_times = 0
                    n_object_times += 1
        if not reverse and object_times > frames: break
        elif reverse and n_object_times > frames: break

def lane_id_det(car, det, lane, id, sp=0.3, scale = 500, timeout=5, region = None, area = None):
    t = time.time()
    while True:
        if time.time() - t > timeout: raise TimeoutError("lane_id_det 超时")
        img = car.cap_side.read()
        if img is None: continue
        img2 = car.cap_front.read()
        if img2 is None: continue
        if region is not None: img = mask_img(img, region)

        dev = lane.predict(img2)/scale
        angle_speed = car.pid_lane(dev)
        car.set_velocity(sp, 0, angle_speed)
        det_res = det.predict_area(img)
        if len(det_res)!=0:
            for res in det_res:
                if int(res[0])==id:
                    if (area is None) or (area is not None and res[1] > area[0] and res[1] < area[1]):return


def lane_any_det(car, det, lane, sp=0.3, scale = 500, timeout=5):
    t = time.time()
    while True:
        if time.time() - t > timeout: raise TimeoutError("lane_any_det 超时")
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
            if boxes is None or len(boxes)==0:continue
            else:break

def lane_not_det(car, det, lane, id, sp=0.3, scale = 500, timeout=5, frames = 3):
    t = time.time()
    nums = 0
    while True:
        if time.time() - t > timeout: raise TimeoutError("lane_any_det 超时")
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
            if not (boxes is None or len(boxes)==0):
                f = False
                for box in boxes:
                    if int(box[0])==id:
                        f = True
                        break
                if f:continue
        nums+=1
        if nums > frames:break

def lane_until_precise(car, det, lane, sp, ids = [0], pre = 0.9, dis_tho = [0, float('inf')], area_tho = [0, float('inf')], timeout=5, scale = 500):
    t = time.time()
    while True:
        if time.time() - t > timeout: raise TimeoutError("lane_until_precise 超时")
        img = car.cap_front.read()
        if img is None: continue
        result = det.predict_precise(img, ids, pre, dis_tho, area_tho)
        if result: break
        dev = lane.predict(img)/scale
        angle_speed = car.pid_lane(dev)
        car.set_velocity(sp, 0, angle_speed)

def lane_until_time(car, lane, sp, wait_time, dev_tho = None, dev_y = 0, timeout=8, scale = 500):
    time1 = time.time()
    while True:
        if time.time() - time1 > timeout: raise TimeoutError("lane_until_time 超时")
        img = car.cap_front.read()
        if img is None: continue
        dev = lane.predict(img)
        if (time.time() - time1 > wait_time) or (dev_tho is not None and abs(dev) < dev_tho): break
        dev/=scale
        y_speed = car.pid_lane_y(dev_y)
        angle_speed = car.pid_lane(dev)
        car.set_velocity(sp, y_speed, angle_speed)


def lane_until_dis(car, lane, dis, sp = 0.55, scale = 350):
    pos = list(car.chassis.odom.pose.copy())[0]
    while True:
        if list(car.chassis.odom.pose)[0] - pos > dis:break
        img = car.cap_front.read()
        if img is None: continue
        dev = lane.predict(img)/scale
        angle_speed = car.pid_lane(dev)
        car.set_velocity(sp, 0, angle_speed)