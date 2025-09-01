import time, re, threading
from tasks.utils import *

ans_map = {'A':1,'B':2,'C':3,'D':4}
def has_height_and_weight(text):
    height_terms = ["高", "h", "H", "m", "米", '寸', '识']
    weight_terms = ["重", "w", "W", "g", "斤", "lb", "磅", '识']
    has_height = any(term in text for term in height_terms)
    has_weight = any(term in text for term in weight_terms)
    return has_height and has_weight

def rec_and_answer(car, ocr, chat):
        print("正在识别文本")
        text = ""
        t = time.time()
        while True:
            if time.time() - t > 0.5:
                 text = "这是一段未识别成功的文本，但请你还是要按照要求随便做出一个回答"
                 break
            text = ""
            img = car.cap_side.read()
            if img is None:continue
            res = ocr.predict_lines(img)
            if len(res)==0:continue
            for r in res:text+=r
            if not has_height_and_weight(text):continue
            break

        print("正在大模型答题")
        problem = f"bmi:帮我从我给你的信息中提取身高与体重，并转为m与kg的单位给我(注意单位转换，如'斤->kg', '英寸->m'等)，并用$环绕，格式严格如下例:$1.7m;40kg$，信息为{text}"
        ans = chat_answer(chat, problem)
        numbers = re.findall(r"\d+\.?\d*", ans)
        height = float(numbers[0])
        weight = float(numbers[1])
        bmi = weight / (height*height)
        if bmi < 18.5:ans = 'A'
        elif bmi <=24:ans = 'B'
        elif bmi <= 28:ans = 'C'
        else:ans = 'D'
        print(f"问题: {problem}")
        print(f"回答: {ans}, {bmi}")
        return ans

def bmi_task(tsks, hanota_f = True):
    car = tsks.car
    det_bmi = tsks.det_bmi
    det_tree = tsks.det_tree
    ocr = tsks.ocr
    chat = tsks.chat
    lane = tsks.lane
    lane2 = tsks.lane2
    try:

        print("循迹寻找判定标志")
        try:
            lane_until_det(car, det_tree, lane, 2, 0.55, 0, scale = 350, timeout = (5 if hanota_f else 10))
        except Exception as e:
            raise TimeoutError("寻找判定标志超时", 0)

        print("正在检测目标")
        lane_until_det(car, det_bmi, lane2, 0, 0.4, frames=1, scale = 400)

        
        print("正在对齐目标")
        lane_until_time(car, lane2, 0, 1.5, 1, scale = 350)
        align_det(car, det_bmi, 0, 10, drct = -1)
        car.chassis.odom.reset()

        print("正在撞击目标")
        car.move_dis_precise(-0.13, 0.2, 0)
        car.move_dis_precise(-0.03, 0.2, 2)
        car.move_time([0, 0.2, 0], 0.6)
        car.move_time([0, -0.2, 0], 0.6)
        car.move_dis_precise(0.13, 0.2, 0)

        ans = rec_and_answer(car, ocr, chat)

        print("转动风车回答")
        car.task.bmi_set(ans_map[ans])
        return True
    except Exception as e:
        print(f"运行错误：{e}")
        if len(e.args) > 1 and e.args[1]==0:return True
        else: return False