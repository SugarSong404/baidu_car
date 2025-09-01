import cv2
import numpy as np
import time
import threading
from tasks.utils import *

foods = "青菜 芹菜 豆角 西红柿 西兰花 辣椒 鸡蛋 鸡肉 香菇 豆腐 牛肉 土豆 排骨 茄子 包菜 冬瓜"
id_map = {"A":0,"B":1,"C":3,"D":4,"E":5,"F":6,"G":7,"H":8,"I":9,"J":10,"K":11,"L":12,"M":13,"N":14,"O":15,"P":16}
name_maps = {"A":"青菜","B":"芹菜","C":"豆角","D":"西红柿","E":"西兰花","F":"辣椒","G":"鸡蛋","H":"鸡肉","I":"香菇","J":"豆腐","K":"牛肉","L":"土豆","M":"排骨","N":"茄子","O":"包菜","P":"冬瓜"}
dis_map = {"A":320,"B":320,"C":320,"D":320,"E":320,"F":320,"G":320,"H":320,"I":320,"J":320,"K":320,"L":320,"M":320,"N":320,"O":320,"P":320}
choice_map = {
    '青菜': 'A', '芹菜': 'B', '豆角': 'C', '西红柿': 'D', '西兰花': 'E',
    '辣椒': 'F', '鸡蛋': 'G', '鸡肉': 'H', '香菇': 'I', '豆腐': 'J',
    '牛肉': 'K', '土豆': 'L', '排骨': 'M', '茄子': 'N', '包菜': 'O', '冬瓜': 'P'
}

def align_food(car, det, left, ans, tho = 10, center = 320):
    height = 0
    time1 = time.time()
    while True:
        if time.time() - time1 > 10:
            raise TimeoutError("对齐食材超时")
        img = car.cap_side.read()
        if img is None:continue
        det_res = det.predict(img)
        if det_res is None:continue
        boxes = det_res.get('boxes', [])
        index = -1
        for i, box in enumerate(boxes):
            if int(box[0]) == id_map[ans]:
                index = i
                break

        if index == -1:continue
        box = boxes[index]
        dis = ((box[2] + box[4]) / 2) - center
        height = (box[3] + box[5]) / 2

        if abs(dis) < tho: break
        pid_output = car.pid_align(dis)
        car.set_velocity(-pid_output * left, 0, 0)
    car.set_velocity(0, 0, 0)
    return (0 if height > 220 else 1)

def rec_and_go(car, ocr, chat, det, left = 1):
    desc = "（右）"
    if left==1:
        car.task.arm.set(0.08, 0.015)
        desc = "（左）"
    elif left==-1:car.task.arm.set(0.22, 0.015)

    problem = ""
    print(f"正在识别文本{desc}")
    text1 = rec_ocr(car, ocr, region = [0, 240, 639, 479])
    problem = f"{('food_left:' if left==1 else 'food_right:')}请根据描述判断指的是哪一种食材，如果描述符合多个选项，选择最显著的特征对应的食材 \n食材选项(答案必须在其中)：{foods}\n一定要从形状、颜色多方面要区分相近项，不能不区分或者只考虑一项特征！\n请根据以下描述作答：\n{text1}\n注意：所有的思考过程都要进行并不超过100个字，不小于50字，并在最后给出字母选项回答，并被$环绕，如$白菜$"
    ans = chat_answer(chat, problem)
    ans = choice_map[ans]
    print(f"问题: {problem}")
    print(f"回答: {ans}")

    print(f"正在对齐食材{desc}")
    forward_until_det(car, det, id_map[ans], 0.1, frames = 1)
    height = align_food(car, det, left, ans, tho=10)
    car.task.arm.set(0.15+left*0.04, 0.015)
    align_food(car, det, left, ans, tho=10, center = dis_map[ans])
    car.move_dis_precise(-0.005 if left==1 else 0, 0.05, 0)
    return height, ans

def food_task(tsks):
    car = tsks.car
    det_food = tsks.det_food
    ocr = tsks.ocr
    lane = tsks.lane
    chat = tsks.chat

    ans1 = ""
    ans2 = ""
    food1_flag = False
    food2_flag = False

    try:
        threading.Thread(target=lambda: (car.task.arm.switch_side(-1)), daemon=True).start()
        lane_until_time(car, lane, 0.55, 0.8, dev_tho = None, scale = 350)
        lane_any_det(car, det_food, lane, 0.55, scale = 350)
        lane_until_det(car, det_food, lane, 2, 0.2, scale = 400, frames = 1)
        print("正在对齐文本（右）")
        align_det(car, det_food, 2, 10, region = [0, 240, 639, 479])
        car.chassis.odom.reset()

        try:
            height, ans1 = rec_and_go(car, ocr, chat, det_food, left=-1)
            print("正在夹取食材（右）")
            car.move_from_zero(-0.025, 0.1, 1)
            car.task.my_pick_first(height,1,-1)
            car.move_from_zero(0, 0.1, 1)
            if not check_det(car, det_food, id_map[ans1]):food1_flag = True
        except Exception as e:
            print(e)
            pass

        print("正在对齐文本（左）")
        car.move_from_zero(0, 0.2, 0)
        car.task.arm.switch_side(1)
        car.task.arm.set(0.15, 0.015)

        try:
            height, ans2 = rec_and_go(car, ocr, chat, det_food)
            print("正在夹取食材（左）")
            car.move_from_zero(0.05, 0.1, 1)
            car.task.my_pick_food_second(height,1)
            car.move_from_zero(0, 0.1, 1)
            if not check_det(car, det_food, id_map[ans2]):food2_flag = True
        except Exception as e:
            print(e)
            pass

        return (name_maps[ans1] if food1_flag else None), (name_maps[ans2] if food2_flag else None), 
    except Exception as e:
        car.task.arm.set(0.15, 0.015)
        car.task.arm.switch_side(1)
        print(f"运行错误：{e}")
        return None, None


    
    
