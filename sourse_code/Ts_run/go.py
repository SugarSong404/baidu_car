import os, sys, time
import numpy as np
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Ts_code import Det, LaneReg, Ocr, Chat
from tasks import *
from ts_car import IdealCar

class Tasks:
    def __init__(self):
        self.car = IdealCar()
        self.car.beep()
        self.car.screen.show("tree")
        self.det_tree = Det("tree")
        self.car.screen.show("bag")
        self.det_bag = Det("bag")
        self.car.screen.show("edu")
        self.det_edu = Det("edu")
        self.car.screen.show("bmi")
        self.det_bmi = Det("bmi")
        self.car.screen.show("mys")
        self.det_mys = Det("mys")
        self.car.screen.show("final")
        self.det_final = Det("final")
        self.car.screen.show("hanota")
        self.det_hanota = Det("hanota")
        self.car.screen.show("food")
        self.det_food = Det("food")
        self.car.screen.show("arrow")
        self.det_arrow = Det("arrow")
        self.car.screen.show("lane-main")
        self.lane = LaneReg("main")
        self.car.screen.show("lane-ann")
        self.lane2 = LaneReg("ann")
        self.car.screen.show("ocr")
        self.ocr = Ocr()
        self.car.screen.show("chat")
        self.chat = Chat()

        self.car.screen.show("warmup")
        test_img = np.zeros((480, 640, 3), dtype=np.uint8)
        self.det_tree.predict(test_img)
        self.det_arrow.predict(test_img)
        self.det_bmi.predict(test_img)
        self.det_edu.predict(test_img)
        self.det_bag.predict(test_img)
        self.det_final.predict(test_img)
        self.det_food.predict(test_img)
        print("目标检测模型预热完毕", flush = True)
        self.lane.predict(test_img)
        self.lane2.predict(test_img)
        print("循迹模型预热完毕", flush = True)
        self.ocr.predict(test_img)
        self.chat.predict("user:1+1=2?A.正确，B.错误，回答选项为字母，请用$包裹")
        print("文本答题模型预热完毕", flush = True)

        self.car.screen.show("all ready")

    def wait_go(self):
        self.car.chassis.odom.reset()
        self.car.task.arm.set(0.15, 0.015)
    
    def run(self):
        self.car.task.arm.reset()
        while True:
            self.car.key_error = True
            self.car.task.arm.set_hand_angle(19)
            self.car.task.arm.switch_side(1)
            self.car.task.bmi_set(0)
            self.car.task.arm.grap(0)
            self.car.task.arm.set(0.15, 0.07)
            key = 0
            while(key==0):
                key = self.car.key.get_key()
                time.sleep(0.01)
            try:
                t = time.time()
                if key == 1:
                    self.wait_go()
                    drct = timed_call(fork_task, self)
                    timed_call(hanota_task, self, drct)
                    ann_flag = timed_call(bmi_task, self)
                    timed_call(ann_task, self, True)
                    timed_call(mys_task, self)
                    timed_call(bag_task, self, 0)
                    food1, food2  = timed_call(food_task, self)
                    timed_call(edu_task, self, food2)
                    has_bag = timed_call(bag_task, self, 1)
                    timed_call(cook_task, self, [food1, food2], has_bag)
                    timed_call(final_task, self, True)
                elif key == 3:
                    self.wait_go()
                    drct = timed_call(fork_task, self)
                    ann_flag = timed_call(bmi_task, self, False)
                    timed_call(ann_task, self, True)
                    timed_call(bag_task, self, 0)
                    food1, food2  = timed_call(food_task, self)
                    timed_call(edu_task, self, food2)
                    has_bag = timed_call(bag_task, self, 1)
                    timed_call(cook_task, self, [food1, food2], has_bag)
                    timed_call(final_task, self, True)
                elif key == 2:
                    self.wait_go()
                    drct = timed_call(fork_task, self)
                    timed_call(ann_task, self, False)
                    food1, food2  = timed_call(food_task, self)
                    has_bag = timed_call(bag_task, self, 1)
                    timed_call(cook_task, self, [food1, food2], has_bag)
                    timed_call(final_task, self, True)

                total = time.time() - t
                self.car.screen.show(str(total))
                print(f"\n总共耗时 {total}s\n")
            except Exception as e:
                self.car.screen.show("error")
                print(e)

if __name__ == '__main__':
    tsks = Tasks()
    tsks.run()

