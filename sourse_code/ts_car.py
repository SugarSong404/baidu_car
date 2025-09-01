import os, time, math, sys, threading
import numpy as np
from Baidu_code import CarBase, Beep, Key4Btn, Camera, ScreenShow
from simple_pid import PID
from task_func import MyTask
sys.path.append(os.path.abspath(os.path.dirname(__file__))) 

class IdealCar(CarBase):
    def __init__(self):
        super(IdealCar, self).__init__()
        self.task = MyTask()
        self.ring = Beep()
        self.pid_lane = PID(Kp= 12,Ki= 0,Kd= 0.9,setpoint= 0,output_limits= [-100, 100])
        self.pid_lane_y = PID(Kp= 4.2,Ki= 0,Kd= 0,setpoint= 0,output_limits= [-0.7, 0.7])
        self.pid_align = PID(Kp= 0.0015,Ki= 0,Kd= 0,setpoint= 0,output_limits= [-0.2, 0.2])
        self.pid_align_bag = PID(Kp= 0.0035,Ki= 0,Kd= 0,setpoint= 0,output_limits= [-0.35, 0.35])
        self.pid_align_end = PID(Kp= 0.0025,Ki= 0,Kd= 0,setpoint= 0,output_limits= [-0.12, 0.12])
        self.screen = ScreenShow()
        self.cap_front = Camera(1)
        self.cap_side = Camera(2)
        self.key = Key4Btn(1)
        self.beep()
        self.key_error = True
        self.thread_key = threading.Thread(target=self.key_thread_func, daemon=True)
        self.thread_key.start()
        print("车辆 idealist 已经完成初始化")

    def key_thread_func(self):
        while True:
            key_val = self.key.get_key()
            if key_val == 4:self.key_error = False
            time.sleep(0.2)

    def beep(self):
        self.ring.rings()
        time.sleep(0.2)

    def set_pose(self, pose, during=None, vel=[0.15, 0.15, math.pi/3], threshold=[0.004, 0.004, 0.02]):
        if during is not None:
            vel = (np.abs(np.array(pose) - self.chassis.odom.pose)) / during
        self.pid_x.setpoint = pose[0]
        self.pid_x.output_limits = (-vel[0], vel[0])
        self.pid_y.setpoint = pose[1]
        self.pid_y.output_limits = (-vel[1], vel[1])
        self.pid_yaw.setpoint = pose[2]
        self.pid_yaw.output_limits = (-vel[2], vel[2])

        pose_threshold = np.array(threshold)

        count_exit = 0
        last_pose = np.array(self.chassis.odom.pose)
        last_move_time = time.time()
        still_threshold = np.array([0.001, 0.001, 0.002]) 

        while True:
            pose_now = np.array(self.chassis.odom.pose)
            err = np.abs(pose_now - pose)
            if (err < pose_threshold).all():
                count_exit += 1
                if count_exit > 20:
                    break
            else:count_exit = 0

            if np.all(np.abs(pose_now - last_pose) < still_threshold):
                if time.time() - last_move_time > 1.5:break
            else:
                last_pose = pose_now
                last_move_time = time.time()

            vel_x_pid = self.pid_x(pose_now[0])
            vel_y_pid = self.pid_y(pose_now[1])
            vel_yaw_out = self.pid_yaw(pose_now[2])
            vel_out = self.sp_world2car([vel_x_pid, vel_y_pid, vel_yaw_out], pose_now[2])
            self.set_velocity(*vel_out)
        self.set_velocity(0, 0, 0)


    def set_pose_single(self, target, axis=0, during=None, vel=0.15, threshold=0.004):
        pid_map = {
            0: self.pid_x,
            1: self.pid_y,
            2: self.pid_yaw,
        }
        pid = pid_map[axis]
        current_val = self.chassis.odom.pose[axis]
        if during is not None:vel = abs(target - current_val) / during
        pid.setpoint = target
        pid.output_limits = (-vel, vel)
        count_exit = 0
        while True:
            current_val = self.chassis.odom.pose[axis]
            err = abs(current_val - target)
            if err < threshold:
                count_exit += 1
                if count_exit > 20:
                    break
            else:
                count_exit = 0
            vel_out = pid(current_val)
            vel_cmd = [0, 0, 0]
            vel_cmd[axis] = vel_out
            self.set_velocity(*vel_cmd)
        self.set_velocity(0, 0, 0)

    def set_world_offset(self, pose, during=None, vel=[0.2, 0.2, math.pi/3], threshold=[0.002, 0.002, 0.02]):
        start_pos = self.chassis.odom.pose
        tar_pos = [0, 0, 0]
        tar_pos[0] = start_pos[0] + pose[0]
        tar_pos[1] = start_pos[1] + pose[1]
        tar_pos[2] = start_pos[2] + pose[2]
        self.set_pose(tar_pos, during, vel, threshold)

    def move(self, ps, sps):
        ps[2]*=math.pi
        sps[2]*=math.pi
        self.set_world_offset(ps, vel = sps, threshold=[0.004, 0.007, 0.02])

    def move_time(self, vel, during):
        time1 = time.time()
        while True:
            if time.time() - time1 > during:break
            self.set_velocity(*vel)
        self.set_velocity(0, 0, 0)

    def move_from_zero(self, p, sp, axis, threshold = None):
        ths=[0.004, 0.004, 0.02]
        if threshold is not None:ths[axis] = threshold
        if axis==2:
            p*=math.pi
            sp*=math.pi  
        self.set_pose_single(p, axis, vel=sp, threshold=ths[axis])

    def move_dis_precise(self, p, sp, axis):
        ths = [0.004, 0.007, 0.02]
        pos = [0, 0, 0]
        v = [0, 0, 0]
        if axis==2:
            p*=math.pi
            sp*=math.pi
        pos[axis] = p
        v[axis] = sp
        self.set_world_offset(pos, vel=v, threshold = ths)