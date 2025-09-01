#!/usr/bin/python3
# -*- coding: utf-8 -*-
# 开始编码格式和运行环境选择

import shutil

import math, time
import numpy as np

from threading import Thread
import yaml, os, sys
# 添加上本地目录
dir_this = os.path.abspath(os.path.dirname(__file__))
sys.path.append(dir_this) 
# 添加上两层目录
dir_root = os.path.abspath(os.path.join(dir_this, ".."))
sys.path.append(dir_root) 

from tools_v import get_yaml, limit_val, CountRecord, PID
import yaml
from Baidu_code import AnalogInput, MotorWrap, Key4Btn, ServoPwm, ServoBus, StepperWrap, Beep, PoutD
# 导入自定义log模块
from tools_v.log_info import logger

def get_path_relative(*args):
    local_dir = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(local_dir, *args)

class ArmBase():
    def __init__(self) -> None:

        self.yaml_path = get_path_relative("arm_cfg.yaml")
        # file_cfg = open(self.yaml_path, 'r')
        with open(self.yaml_path, 'r') as f:
            self.config = yaml.load(f, Loader=yaml.FullLoader)

        self.vert_params_init(**self.config["vert_cfg"])
        self.horiz_params_init(**self.config["horiz_cfg"])
        self.hand_params_init(**self.config["hand_cfg"])
        self.pos_params_init(**self.config["pos_cfg"])
        # self.arm_servo = ServoBus(self.config["hand_cfg"]["hand"]["port"])
        self.horiz_dis = 0.27
        self.horiz_mid = self.horiz_dis / 2
        # 位置调整
        if self.side == 0:
            logger.info("hand init")
            self.switch_side(-1)
        # self.arm_servo.set_angle(50, 90)
    
    # 定义竖直移动电机 限位传感器，速度转换参数
    # def vert_params_init(self, motor, limit_port, pid, threshold):
    def vert_params_init(self, motor, limit_port, pid, threshold):
        self.vert_motor = StepperWrap(**motor)
        self.vert_limit_sensor = AnalogInput(limit_port)
        
        self.vert_pose_start = self.vert_motor.get_dis()
        self.vert_pose_now = 0
        self.vert_pid = PID(**pid)
        self.vert_vel_limit = pid['output_limits']
        self.vert_d_dis = 0
        self.vert_threshold = threshold
        self.vert_pose_last = 0

        self.vert_pid_flag = CountRecord(5)
        self.vert_stop_flag = CountRecord(10)

    def vert_reset_check(self):
        return self.vert_limit_sensor.read() > 1000

    def vert_stop_check(self):
        return self.vert_stop_flag(abs(self.vert_d_dis) < 1e-10)

    def vert_pid_move(self, pose):
        # 记录编码值，并更新上次的编码值
        self.vert_pose_now = self.vert_motor.get_dis() - self.vert_pose_start
        self.vert_d_dis = self.vert_pose_now - self.vert_pose_last
        self.vert_pose_last = self.vert_pose_now

        err = pose - self.vert_pose_now
        vel = self.vert_pid(self.vert_pose_now)

        self.vert_speed(vel)
        # print('vert now:', self.vert_pose_now, "dis:", self.vert_d_dis, "err:", err, "vel:",vel)
        if self.vert_pid_flag(abs(err)< 4e-4):
            return True
        else:
            return False
    
    def reset_vert(self):
        
        self.vert_pid.setpoint = -0.25
        while True:
            if self.vert_pid_move(-0.25):
                break
            if self.vert_reset_check():
                self.vert_pose_start = self.vert_motor.get_dis()
                self.vert_pose_now = 0
                break
        self.vert_speed(0)

    def move_vert_dis(self, tar):
        self.vert_pid.setpoint = tar
        while True:
            if self.vert_pid_move(tar):
                break
        self.vert_speed(0)
        # print(self.vert_motor.get_dis() - self.vert_pose_start)
        

    def horiz_params_init(self, motor, pid, threshold):
        # 定义水平移动电机,PID参数
        self.horiz_motor = MotorWrap(**motor)
        self.horiz_pid = PID(**pid)
        self.horiz_vel_limit = pid['output_limits']
        self.horiz_pose_start = self.horiz_motor.get_dis()
        self.horiz_pose_now = 0
        self.horiz_threshold = threshold
        self.horiz_pose_last = 0

        self.horiz_d_dis = 0

        self.horiz_stop_flag = CountRecord(10)
        self.horiz_pid_flag = CountRecord(5)
    
    def horiz_stop_check(self):
        return self.horiz_stop_flag(abs(self.horiz_d_dis) < 1e-10)
    
    def horiz_pid_move(self, pose):
        
        self.horiz_pose_now = self.horiz_motor.get_dis() - self.horiz_pose_start
        self.horiz_d_dis = self.horiz_pose_now - self.horiz_pose_last        
        self.horiz_pose_last = self.horiz_pose_now
        err = pose - self.horiz_pose_now

        vel = self.horiz_pid(self.horiz_pose_now)

        self.horiz_speed(vel)
        # print('horiz_motor now:', self.horiz_pose_now, "dis:",self.horiz_d_dis, "err:", err, "vel:",vel)
        if self.horiz_pid_flag(abs(err)< 4e-4):
                return True
        else:
            return False
    
    def move_horiz_dis(self, tar):
        self.horiz_pid.setpoint = tar
        while True:
            if self.horiz_pid_move(tar):
                break
            if self.horiz_stop_check():
                self.horiz_pose_start = self.horiz_motor.get_dis()
                break
        self.horiz_speed(0)
        # self.beep.rings()
        
    def reset_horiz(self):
        tar = -0.25
        self.horiz_pid.output_limits = (-0.06, 0.06)
        self.horiz_pid.setpoint = tar
        while True:
            if self.horiz_pid_move(tar):
                break
            if self.horiz_stop_check():
                self.horiz_pose_start = self.horiz_motor.get_dis()
                self.horiz_pose_now = 0
                self.horiz_pose_last = 0
                break
        self.horiz_speed(0)
        # print(self.horiz_motor.get_dis() - self.horiz_pos_start)
        # self.beep.rings()
    
            
    def hand_params_init(self, hand, hand2, grap):
        self.hand_servo = ServoPwm(hand2["port"], mode=270)
        self.hand_list2 = hand2["angle_list"]
        # self.hand_servo.set_angle(-45, 90)
        self.arm_servo = ServoBus(hand["port"])
        self.hand_list = hand["angle_list"]
        self.pump = PoutD(grap["port_pump"])
        self.valve = PoutD(grap["port_valve"])

    def grap(self, val):
        self.pump.set(val)
        self.valve.set(not val)
        time.sleep(0.1)

    # 设置手部舵机的角度
    def set_hand_angle(self, angle):
        # 将手部舵机的角度设置为传入的参数angle，速度为90
        self.hand_servo.set_angle(angle, 90)

    def switch_hand_dir(self, side):
        self.set_hand_angle(self.hand_list2[side])

    def pos_params_init(self, pose_enable, pose_horiz, pose_vert, side):
        self.pose_enabale = pose_enable
        self.vert_pose_start = self.vert_motor.get_dis() - pose_vert
        self.vert_pose_now = pose_vert
        self.horiz_pose_start = self.horiz_motor.get_dis() - pose_horiz
        self.horiz_pose_now = pose_horiz
        self.side = side
    
    def save_yaml(self, pose_enable=True):
        # logger.info("side:{}".format(self.side))
        self.config["pos_cfg"] = {"pose_enable":pose_enable, "pose_horiz":self.horiz_pose_now, "pose_vert":self.vert_pose_now, "side": self.side}
        with open(self.yaml_path, 'w') as stream:
            yaml.dump(self.config, stream, sort_keys=False)

    def vert_speed(self, vel_vert):
        vel_vert = limit_val(vel_vert, *self.vert_vel_limit)
        self.vert_motor.set_velocity(vel_vert)
    
    def horiz_speed(self, vel_horiz):
        vel_horiz = limit_val(vel_horiz, *self.horiz_vel_limit)
        self.horiz_motor.set_linear(vel_horiz)

    def set_pos_start(self, pos_vert):
        self.vert_pose_start = self.vert_pose_now
        self.horiz_pose_start = self.horiz_pose_now
        self.save_yaml()

    def set_by_yourself(self):
        self.key = Key4Btn(4)
        logger.info("set arm by yourself...")
        while True:
            val = self.key.get_key()
            if val == 1:
                self.vert_speed(0.1)
            elif val == 3:
                self.vert_speed(0.1)
            elif val == 4:
                self.horiz_speed(0.1)
            elif val == 2:
                self.horiz_speed(0.1)
            else:
                self.horiz_speed(0)
                self.vert_speed(0)
            # time.sleep(0.1)
                          
    def reset(self):
        self.grap(0)
        thread_reset_v = Thread(target=self.reset_vert)
        thread_reset_h = Thread(target=self.reset_horiz)
        self.side = -1
        self.switch_side(1)
        thread_reset_v.setDaemon(True)
        thread_reset_h.setDaemon(True)
        thread_reset_v.start()
        thread_reset_h.start()
        thread_reset_v.join()
        thread_reset_h.join()
        self.save_yaml()
        # self.reset_pos_dir(2, 0.04)
        # 回到初始位置
        self.set_hand_angle(20)
    def switch_side(self, side):
        if self.side != side:
            self.side = side
            logger.info("change side to {}".format(self.side))
            # print("change side to {}".format(self.side))
        else:
            return
        angle_tar = self.hand_list[side]
        # print(angle_tar)
        self.set_arm_angle(angle_tar, 80)
        time.sleep(0.5)
    
    def reset_pos_dir(self, dir=0, speed=0.1):
        horiz_flag = False
        vert_flag = False
        if dir == 0:
            # 只复位水平位置
            vert_flag = True
        elif dir == 1:
            # 只复位竖直位置
            horiz_flag = True
        while True:
            if vert_flag and horiz_flag:
                break
            if horiz_flag is False:
                self.horiz_motor.get_dis()
                if self.horiz_stop_check():
                    self.horiz_speed(0)
                    self.horiz_pose_now = 0
                    self.horiz_pose_start = 0
                    self.horiz_motor.reset()

                    self.horiz_pose_start = 0
                    self.horiz_pose_now = 0
                    horiz_flag = True
                else:
                    pass
                    self.horiz_speed(speed)

            if vert_flag is False:
                if self.vert_reset_check():
                    self.vert_speed(0)
                    self.vert_motor.reset()

                    self.horiz_pose_start = 0
                    self.vert_pose_now = 0
                    vert_flag = True
                else:
                    self.vert_speed(0-abs(speed))


    def set_arm_angle(self, angle, speed=80):
        # 设置
        self.arm_servo.set_angle(angle, speed)
        for key, val in self.hand_list.items():
            if val == angle:
                self.side = key
                break
        else:
            self.side = 0
        self.save_yaml()
    
    def set_arm_dir(self, dir=0, speed=80):
        assert dir == 0 or dir == 1 or dir == -1, "dir should be 0 or 1 or -1"
        self.set_arm_angle(self.hand_list[dir], speed)


    def set_offset(self, horiz_offset, vert_offset, time_run=None, speed=[0.15, 0.04]):
        horiz_pos = self.horiz_pose_now + horiz_offset
        vert_pos = self.vert_pose_now + vert_offset
        self.set(horiz_pos, vert_pos, time_run, speed)

    def set(self, horiz_pos, vert_pos, time_run=None, speed=[0.15, 0.04]):
        # print(horiz_pos)
        # 控制上下限
        horiz_pos = limit_val(horiz_pos, self.horiz_threshold[0], self.horiz_threshold[1])
        # print(horiz_pos)
        vert_pos = limit_val(vert_pos, self.vert_threshold[0], self.vert_threshold[1])
        
        # 获取结束时间和对应速度
        time_start = time.time()
        if time_run is not None:
            assert isinstance(time_run, int) or isinstance(time_run, float), "wrong time args"
            # 根据时间求速度
            time_end = time_start + time_run
            vert_time = time_run
            horiz_time = time_run
        elif speed is not None:
            # 根据速度求时间
            if isinstance(speed, int) or isinstance(speed, float):
                # print(speed)
                speed_horiz = speed
                speed_vert = speed
            elif isinstance(speed, list) or isinstance(speed, tuple):
                speed_horiz = speed[0]
                speed_vert = speed[1]
            else:
                logger.error("wrong speed args")
                return
            horiz_time = abs(horiz_pos - self.horiz_pose_now) / speed_horiz
            vert_time = abs(vert_pos - self.vert_pose_now) / speed_vert
            time_run = max(horiz_time, vert_time)
            # print("time run:", time_run)
        else:
            logger.error("wrong args")
            return
        # 超时时间
        time_end = time_start + time_run

        # 定义结束标志和到达位置标记量
        vert_flag = False
        horiz_flag = False

        # 获取对应的速度和pid位置
        if vert_time < 0.1:
            speed_vert = 0.1
            vert_flag = True
        else:
            speed_vert = abs(vert_pos - self.vert_pose_now) / vert_time
        
        self.vert_pid.setpoint = vert_pos
        self.vert_pid.output_limits = (-speed_vert, speed_vert)
        
        if horiz_time < 0.1:
            speed_horiz = 0.1
            horiz_flag = True
        else:
            speed_horiz = abs(horiz_pos - self.horiz_pose_now) / horiz_time
        # print("speed_horiz:", speed_horiz, "speed_vert:", speed_vert)
        self.horiz_pid.setpoint = horiz_pos
        self.horiz_pid.output_limits = (-speed_horiz, speed_horiz)
        # 开始移动前，位置信息定义，如果中间中断此时位置信息无用
        self.save_yaml(pose_enable=False)
        while True:
            # 到达结束标志结束
            if vert_flag and horiz_flag:
                break
            # 获取剩余时间
            time_remain = time_end - time.time()
            # print("time remain:", time_remain)
            # 超时处理
            if time_remain < -2:
                logger.warning("timeout")
                # 超时停止
                self.horiz_speed(0)
                self.vert_speed(0)
                break
            if not vert_flag:
                if self.vert_pid_move(vert_pos):
                    self.vert_speed(0)
                    vert_flag = True

                # 重置初始化位置
                if self.vert_reset_check():
                    if self.vert_pid.setpoint <= self.vert_pose_now:
                        vert_flag = True
                        self.vert_speed(0)
                    self.vert_pose_start = self.vert_motor.get_dis()
                    self.vert_pose_now = 0
                    self.save_yaml()
            
            if not horiz_flag: 
                if self.horiz_pid_move(horiz_pos):
                    self.horiz_speed(0)
                    horiz_flag = True
                # elif self.horiz_stop_check():
                #     self.horiz_pose_start = self.horiz_motor.get_dis()
                #     self.horiz_pose_now = 0
                #     self.save_yaml()
            # time.sleep(0.005)
        self.save_yaml()
        # logger.debug("pos vert:{}, horiz:{}".format(self.vert_pose_now, self.horiz_pose_now))


if __name__ == '__main__':
    # ser = SerialWrap()
    arm = ArmBase()
    
    st = time.time()
    # arm.reset_horiz()
    # arm.reset_vert()
    # arm.move_horiz_dis(0.1)
    
    arm.reset()
    # arm.set(0.132, 0.075, speed=[0.06,0.08])
    
    # arm.set_hand_angle(-45)
    arm.set(0.2, 0.02)
    # arm.grap(1)
    # arm.set(0.26, 0.10)
    
    # arm.set_offset(-0.08, 0.02, speed=[0.1, 0.04])
    # # arm.set_off(0.04, 0, speed=[0.1, 0.4])
    # arm.set_hand_angle(48)
    # arm.set(0.005, 0.02, speed=[0.1, 0.04])
    # time.sleep(0.5)
    # arm.grap(0)
    print(time.time() - st)
    # # arm.set(0.1, 0.05, speed=[0.06,0.025])
    # arm.grap(1)
    # arm.set_offset(0.01, 0, 0.3)
    # time.sleep(1)

    # arm.set_offset(0, 0.08, 2.5)
    # time.sleep(2)
    # arm.set_arm_angle(90)
    # arm.switch_side(1)
    # for i in range(10):
    #     arm.switch_side(1)
    #     time.sleep(2)
    #     arm.switch_side(-1)
    #     time.sleep(2)
    # arm.grap(0)
    # time.sleep(1)
    # arm.switch_side(1)
    print(arm.horiz_pose_now, arm.vert_pose_now)
    # arm.move_vert_dis(0.1)
    # arm.set(0.1, 0.1, 2.5)
    # arm.set_offset(0, 0.04, 2)
    # arm.move_vert_dis(-0.04)
    # arm.reset_horiz()
    # arm.set_by_yourself()
    # while True:
    #     # arm.set_arm_angle(0)
    #     # arm.set_arm_dir(0)
    #     arm.set(0, 0.05, 1)
    #     # arm.set_arm_angle(-52)
    #     time.sleep(1)
    #     arm.set(0, 0.1, 1)
    #     # arm.set_arm_angle(90)
    #     # arm.set_arm_dir(-1)
    #     time.sleep(1)
    #     arm.set(-0.05, 0.1, 1)
    #     time.sleep(1)
    # arm.reset()
    
    # car.pull_init()
    # while True:
    #     arm.set(0, 0.05, 1)
    #     time.sleep(1)
    #     arm.set(0, 0.1, 1)
    #     time.sleep(1)
    #     arm.set(-0.1, 0.1, 1)
    #     time.sleep(1)
    #     arm.set(0, 0.1, 1)
    #     time.sleep(1)

    # car.pull_down()
    # arm  = ArmBase(ser)
    # arm.reset()
    # arm.horiz_moto.set(-20)
    # arm.set(-0.15, 0.1, 2)
    # arm.set_by_yourself()
    # count = 0
    # time.sleep(5)
    # print("time cost:", time.time() - last_time)
    # print(count)
