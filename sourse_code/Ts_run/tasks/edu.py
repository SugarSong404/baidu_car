import numpy as np
import threading
import time
from tasks.utils import *

dis_map = {'A':-0.13,'B':-0.05,'C':0.05,'D':0.13}
dis_map2 = {'A':-0.135,'B':-0.05,'C':0.03,'D':0.13}

def rec_and_answer(car, ocr, chat):
    print("正在识别题目")
    text1 = rec_ocr(car, ocr,region = [0, 0, 639, 235])

    print("正在识别选项")
    texts = rec_ocr_multi(car, ocr, region = [0, 235, 639, 479], num = 4, exit_f = False)


    print("正在文本答题")
    problem = f"edu:{text1}，仔细分析，并从下列选项中选择正确的一项回答该问题, A.{texts[0]} B.{texts[1]} C.{texts[2]} D.{texts[3]}\n注意：思考过程都要进行并不超过100个字，不小于50字，并在最后给出选项回答，并被$环绕，如$A$"
    ans = chat_answer(chat, problem)
    print(f"问题: {problem}")
    print(f"回答: {ans}")
    return ans


def edu_task(tsks, food2):
    car = tsks.car
    det = tsks.det_edu
    ocr = tsks.ocr
    chat = tsks.chat
    lane = tsks.lane
    try:
        has_obj = food2 is None
        print("调整摄像头位置")
        threading.Thread(target=lambda: (car.task.arm.set(0.13, 0.07)), daemon=True).start()
        lane_id_det(car, det, lane, 0, sp=0.55, scale = 350, timeout=10, area = [50000, 100000])
        
        print("正在对齐题目")
        align_det(car, det, 0, 10, drct=-1, frames=5)

        ans = rec_and_answer(car, ocr, chat)
        print("对齐正确选项")
        car.chassis.odom.reset()
        car.move_from_zero(dis_map2[ans] if has_obj else dis_map[ans], 0.1, 0)
        car.move_from_zero(0.05 if has_obj else 0.025, 0.1, 1)
        if has_obj:car.task.arm.set(0.15, 0.061)
        else:car.task.arm.set(0.15, 0.072)
        car.task.educate_push()
        car.move_from_zero(0, 0.1, 1)
    except Exception as e:
        tsks.car.task.arm.set(0.15, 0.05)
        print(f"运行错误：{e}")
