from tasks.utils import *
import time

ans_map = {"A":0,"B":1,"C":2,"D":3}
def cook_task(tsks, foods, has_bag):
    car = tsks.car
    det_food = tsks.det_food
    ocr = tsks.ocr
    lane = tsks.lane
    chat = tsks.chat
    if (foods[0] is None and foods[1] is None) or (not has_bag):return
    try:
        print("正在拉正车身")
        car.task.arm.switch_side(-1)
        car.task.arm.set_hand_angle(-65)
        car.task.arm.set(0.15, 0.04)
        lane_until_time(car, lane, 0, 1.5, 1, scale = 350)

        print("正在识别前两段文本")
        cooks = []
        align_det(car, det_food, 2, 10, region = [0, 232, 639, 479])
        text = rec_ocr(car, ocr, 0.95, [0, 232, 639, 479])
        cooks.append(text)

        text = rec_ocr(car, ocr, 0.95, [0, 0, 639, 232])
        cooks.append(text)

        print("正在大模型匹配")
        problem = f"cook:我有 {foods[0]} 与 {foods[1]} 这两种食材，以下给你两个菜品描述，选出最符合这两道食材做出的菜品特征的一项（可以先想出菜名再给出选项，如果该特征不符合两道食材可以制作的菜品，请选择C）：\nA.{cooks[0]}\nB.{cooks[1]}C.没有对应的菜品\n注意：思考过程都要进行并不超过100个字，不小于50字，并在最后给出选项回答，并被$环绕，如$A$"
        ans = chat_answer(chat, problem)
        
        print(f"问题：{problem}")
        print(f"回答：{ans}")
        if ans!="A" and ans!="B":
            print("正在前往后方文本")
            car.chassis.odom.reset()
            lane_until_dis(car, lane, 0.20, sp = 0.3, scale = 500)
            lane_id_det(car, det_food, lane, 2)

            print("正在识别后两段文本")
            align_det(car, det_food, 2, 10, region = [0, 232, 639, 479])
            text = rec_ocr(car, ocr, 0.95, [0, 232, 639, 479])
            cooks.append(text)

            text = rec_ocr(car, ocr, 0.95, [0, 0, 639, 232])
            cooks.append(text)

            print("正在大模型匹配")
            problem = f"cook:我有 {foods[0]} 与 {foods[1]} 这两种食材，以下给你两个菜品描述，选出最符合这两道食材做出的菜品特征的一项（可以先想出菜名再给出选项，如果该特征不符合两道食材可以制作的菜品，请选择E）：\nC.{cooks[2]}\nD.{cooks[3]}E.没有对应的菜品\n注意：思考过程都要进行并不超过100个字，不小于50字，并在最后给出选项回答，并被$环绕，如$C$"
            ans = chat_answer(chat, problem)
            print(f"问题：{problem}")
            print(f"回答：{ans}")
        if ans=="E": return
        
        height = ans_map[ans] % 2
        drct = int(ans_map[ans]/2)
        print("正在放置")
        car.chassis.odom.reset()

        dis = 0.057
        dis2 = 0.067
        if drct==1:
            dis = -0.067
            dis2 = -0.077
        else:car.move_dis_precise(-0.01, 0.05, 1)
        car.move_dis_precise(dis, 0.1, 0)
        car.task.arm.grap(1) 
        if foods[0] is not None:
            car.task.set_food2(1,height+1)
        if foods[1] is not None:
            car.move_dis_precise(dis2, 0.1, 0)
            car.task.set_food2(2,height+1)
    except Exception as e:
        car.task.arm.set(0.15, 0.015)
        car.task.arm.switch_side(1)
        print(f"运行错误：{e}")

