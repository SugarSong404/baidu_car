from Baidu_code import ArmBase, ServoBus, MotorWrap, StepperWrap, PoutD
import time
import math

class Ejection():
    def __init__(self, portm=5, portd=4, port_step=1) -> None:
        self.motor = MotorWrap(portm, -1, type="motor_280", perimeter=0.06/15*8)
        self.pout = PoutD(portd)
        self.step1 = StepperWrap(2)
        self.step_rad_st = self.step1.get_rad()
        self.step1_rad_cnt = 0

    def reset(self, vel=0.05):#改变上升吸取的速度,加速为0.15
        rad_last = self.motor.get_rad()
        
        while True:
            self.motor.set_linear(vel)
            time.sleep(0.02)
            rad_now = self.motor.get_rad()
            if abs(rad_now - rad_last) < 0.02:
                break
            rad_last = rad_now
        
        self.motor.set_linear(0)
        
    def eject(self, x=0.1,num=1,vel=0.05):
        self.reset()
        self.pout.set(1)
        self.motor.reset()
        self.motor.set_linear(0-abs(vel))
        length = 0.1
        while True:
            self.motor.set_linear(0-abs(vel))
            if abs(self.motor.get_dis()) > length:
                break
        self.motor.set_linear(0)
        self.step1_rad_cnt += 1
        self.step1.set_rad(-math.pi/5*2*self.step1_rad_cnt + self.step_rad_st)
        self.pout.set(1)
        time.sleep(0.4)
        while True:
            self.motor.set_linear(abs(vel))
            if abs(self.motor.get_dis()) < x:
                break
        self.motor.set_linear(0)
        self.pout.set(0)

    def my_eject(self, x=0.1,num=1,vel=0.05):
        self.pout.set(1)
        self.reset()
        self.pout.set(1)
        self.motor.reset()
        self.motor.set_linear(0-abs(vel))
        length = 0.1
        while True:
            self.motor.set_linear(0-abs(vel))
            if abs(self.motor.get_dis()) > length:
                break
        self.motor.set_linear(0)
        self.step1_rad_cnt += 1
        self.step1.set_rad(-math.pi/5*2*self.step1_rad_cnt + self.step_rad_st)
        self.pout.set(1)
        time.sleep(0.9)
        while True:
            self.motor.set_linear(abs(vel))
            if abs(self.motor.get_dis()) < x:
                break
        self.motor.set_linear(0)
        time.sleep(0.5)
        self.pout.set(0)

class MyTask:
    def __init__(self):
        # 旋转舵机
        self.servo_bmi = ServoBus(2)            
        # 发射装置
        self.ejection = Ejection()
        time.sleep(0.1)
        # 机械臂
        self.arm = ArmBase()
    def reset(self):
        self.arm.reset()
    
    def my_send1(self, area=1):
        dis_list = {1:0.099, 2:0.061}#2:0.067
        #self.ejection.eject(dis_list[area],area,0.15)#最后一个可加速下拉
        self.ejection.eject(dis_list[area],area)
    def my_send2(self, area=1):
        dis_list = {1:0.087, 2:0.060}#2:0.067
        self.ejection.my_eject(dis_list[area],area,0.07)#最后一个可加速下拉
        #self.ejection.my_eject(dis_list[area],area)#最后一个可加速下拉

    def my_pick_up_cylinder(self, radius, direction=1,arm_set=False):
        down1=[0.068,0.071,0.071]
        up1=[0.17,0.168,0.222]
        if direction==1:pos=0.04
        elif direction==-1:pos=0.26
        self.arm.grap(1)
        
        time.sleep(0.3)
        self.arm.set_hand_angle(15)
        self.arm.set(pos, down1[radius], speed=[0.16, 0.08]) #下降吸取
        self.arm.set(pos, up1[radius], speed=[0.16, 0.08])#抬起一定高度

    def my_put_down_cylinder(self, radius, direction=1):
        if direction==1:pos=0.04
        elif direction==-1:pos=0.26
        
        #if direction==1:ret=0.09
        #elif direction==-1:ret=0.2
        self.arm.set_hand_angle(15)

        down2=[0.077,0.137,0.218]
        up2=[0.1,0.16,0.221]
        self.arm.set(pos, down2[radius], speed=[0.16, 0.08]) #fang
        self.arm.grap(0)
        time.sleep(0.3)
        # 抬起
        self.arm.set(pos,up2[radius], speed=[0.18, 0.06])
        #time.sleep(0.1)
        #self.arm.set(ret,up2[radius], speed=[0.18, 0.05])
        #time.sleep(0.1)
        
    
    def bmi_set(self, num=0):
        bmi = {0:0, 1:-45, 2: -135, 3:45, 4:135}
        self.servo_bmi.set_angle(bmi[num])

    def my_pick_food(self,row,num=1,direction=1, arm_set=False):
        if row==0:
            self.arm.set_offset(0,0)
            self.arm.set(0.15,0)
        elif row==1:
            self.arm.set_offset(0,0.085)
            self.arm.set(0.15, 0.085)
        # 准备抓取
        self.arm.grap(1)    # 手水平
        self.arm.set_hand_angle(-125)
        time.sleep(0.5)
        # 手臂向外伸，去抓取物块
        horiz_offset = 0.14*direction
        horiz_offset2=-0.08*direction
        self.arm.set_offset(horiz_offset, 0)
        if num==1:
            self.arm.set_offset(horiz_offset2,0)
            self.arm.set_offset(0,0.03)
        self.arm.set(0.15, 0.06)
        # 手向下
        self.arm.set_hand_angle(20)
        if num==1:
            # 放下物块
            #self.arm.set_offset(-0.14*self.arm.side, 0, speed=[0.08, 0.04])
            self.arm.set_offset(0, -0.03, speed=[0.12, 0.04])
            self.arm.grap(0)
            self.arm.set_offset(0, 0.03, speed=[0.12, 0.04])

    def my_pick_food2(self,row,num=1,direction=1, arm_set=False):
        if row==0:
            self.arm.set_offset(0,0)
            self.arm.set(0.15,0)
        elif row==1:
            self.arm.set_offset(0,0.085)
            self.arm.set(0.15, 0.085)
        # 准备抓取
        self.arm.grap(1)    # 手水平
        self.arm.set_hand_angle(-125)
        time.sleep(0.2)
        # 手臂向外伸，去抓取物块
        horiz_offset = 0.14*direction
        horiz_offset2=-0.08*direction
        self.arm.set_offset(horiz_offset, 0)
        self.arm.set_offset(horiz_offset2,0)
        if row==0:
            self.arm.set_offset(0,0.03)
        self.arm.set(0.15, 0.06)
        # 手向下
        self.arm.set_hand_angle(20)
        if num==1:
            # 放下物块
            self.arm.set_offset(-direction*0.12,0.04)
            self.arm.set_offset(0, -0.108, speed=[0.12, 0.04])
            self.arm.grap(0)
            self.arm.set_offset(0, 0.108, speed=[0.12, 0.04])
    def my_pick_first(self,row,num=1,direction=1):
        if row==0:
            #self.arm.set_offset(0,0)
            self.arm.set(0.11,0.017)#0.04的变化，因为有精细对齐
        elif row==1:
            #self.arm.set_offset(0,0.10)
            self.arm.set(0.11, 0.10)
        # 准备抓取
        self.arm.grap(1)    # 手水平
        self.arm.set_hand_angle(-125)
        time.sleep(0.5)
        # 手臂向外伸，去抓取物块
        horiz_offset = 0.08*direction
        horiz_offset2=-0.09*direction
        self.arm.set_offset(horiz_offset, 0)
        self.arm.set_offset(horiz_offset2,0)
        if row==0:
            self.arm.set_offset(0,0.03)
        self.arm.set_hand_angle(20)
        self.arm.set(0.285, 0.06)
        # 放下物块
        #self.arm.set_offset(-direction*0.12,0.04)
        self.arm.set_offset(0, -0.055, speed=[0.12, 0.08])
        self.arm.grap(0)
        self.arm.set_offset(0, 0.055, speed=[0.12, 0.08])
        
    def my_pick_food_second(self,row,direction=1):
        if row==0:
            self.arm.set(0.19,0.017)
        elif row==1:
            self.arm.set_offset(0,0.10)
            self.arm.set(0.19, 0.10)
            #self.arm.set_offset(0.03,0)
        # 准备抓取
        self.arm.grap(1)    # 手水平
        self.arm.set_hand_angle(-125)
        time.sleep(0.5)
        # 手臂向外伸，去抓取物块
        horiz_offset = 0.09
        horiz_offset2=-0.08
        self.arm.set_offset(horiz_offset, 0)
        self.arm.set_offset(horiz_offset2,0)
        if row==0:
            self.arm.set_offset(0,0.03)
        self.arm.set(0.15, 0.07)
        # 手向下
        self.arm.set_hand_angle(18)
    def my_pick_food_second2(self,row,direction=1):
        self.arm.set_hand_angle(-125)
        if row==0:
            self.arm.set(0.15,0.05)
            self.arm.set_offset(0.07,-0.03)
            self.arm.grap(1)    # 手水平
            self.arm.set_hand_angle(-125)
            time.sleep(0.5)
            self.arm.set(0.29, 0.02)
            self.arm.set_offset(0.21,0.02)

            self.arm.set_offset(0,0.03)
            self.arm.set(0.15, 0.07)
            # 手向下
            self.arm.set_hand_angle(18)
        elif row==1:
            self.arm.set_offset(0,0.105)
            self.arm.set(0.15, 0.105)
            self.arm.set_offset(0.07,0)
            # 准备抓取
            self.arm.grap(1)    # 手水平
            time.sleep(0.5)
            # 手臂向外伸，去抓取物块
            self.arm.set(0.29, 0.105)
            self.arm.set(0.29,0.105)
            self.arm.set(0.15, 0.07)
            # 手向下
            self.arm.set_hand_angle(18)
    def educate_push(self):
        #self.arm.grap(1)
        #self.arm.switch_side(1)
        #self.arm.set_hand_angle(15)
        self.arm.set_hand_angle(-130) #水平
        time.sleep(0.1)
        self.arm.set_offset(0.12, 0)  #推
        time.sleep(0.1)
        self.arm.set_offset(-0.12, 0) #收
        self.arm.set_hand_angle(15)

    def set_food(self, num=1, row=1, arm_set=False):
        # 气泵吸气并关闭阀门，调整手臂方向向右
        self.arm.grap(1)
        self.arm.switch_side(-1)
        
        if num > 1:     # 如果放的不是第一个，需要先抓取，手朝向下
            self.arm.switch_side(-1)
            # 到达抓取位置，准备抓取
            self.arm.set(0,0.05)
            self.arm.set_hand_angle(15)
            # 向下移动抓取
            self.arm.grap(1)
            self.arm.set_offset(0, -0.05)
            time.sleep(0.1)
            self.arm.set_offset(0, 0.05)# 向上移动
            self.arm.set_hand_angle(-130)# 手臂指向方向调整水平

        if row==1:
            my_height7=0.005#如果水平就是0
        else:
            my_height7=0.095#水平为0.09
        self.arm.set(0.15,my_height7)
        time.sleep(0.2)
        self.arm.set_hand_angle(-125)
        # 手臂向前伸运动0.14m
        self.arm.set_offset(0.10*self.arm.side, 0, speed=[0.12, 0.04])
        self.arm.grap(0)
        time.sleep(0.1) 
        self.arm.set_offset(-0.02*self.arm.side, 0, speed=[0.12, 0.04])
        self.arm.set_offset(0, 0.05, speed=[0.12, 0.1])
        self.arm.set_offset(-0.08*self.arm.side, 0, speed=[0.12, 0.04])

    def set_food2(self, num=1, row=1):
        # 气泵吸气并关闭阀门，调整手臂方向向右
        self.arm.set_hand_angle(-125)
        if num > 1:     # 如果放的不是第一个，需要先抓取，手朝向下
            self.arm.set_hand_angle(15)
            # 到达抓取位置，准备抓取
            self.arm.set(0.28, 0.05)
            # 向下移动抓取
            self.arm.grap(1)
            self.arm.set_offset(0, -0.05)
            time.sleep(0.1)
            self.arm.set_offset(0, 0.05)# 向上移动
            self.arm.set_hand_angle(-130)# 手臂指向方向调整水平
            
            if row==1:
                my_height7=0.017#如果水平就是0
            else:
                my_height7=0.115
        else:
            if row==1:
                my_height7=0.022#如果水平就是0
            else:
                my_height7=0.115
        self.arm.set(0.15,my_height7)
        time.sleep(0.1)
        self.arm.set_hand_angle(-125)
        # 手臂向前伸运动0.14m
        self.arm.set_offset(0.09*self.arm.side, 0, speed=[0.16, 0.04])
        self.arm.grap(0)
        time.sleep(0.1)
        if row==1:
            self.arm.set_offset(-0.03*self.arm.side, 0, speed=[0.16, 0.04])
            self.arm.set_offset(0, 0.03, speed=[0.12, 0.1])
            self.arm.set_offset(-0.07*self.arm.side, 0, speed=[0.16, 0.04])
        else:
            self.arm.set_offset(-0.09*self.arm.side, 0, speed=[0.16, 0.04])

   
    def set_food3(self, num=1, row=1, arm_set=False):
        # 气泵吸气并关闭阀门，调整手臂方向向右
        self.arm.grap(1)
        #self.arm.switch_side(-1)
        
        if num > 1:     # 如果放的不是第一个，需要先抓取，手朝向下
            self.arm.set_hand_angle(15)
            # 到达抓取位置，准备抓取
            self.arm.set(0.29, 0.05)
            self.arm.switch_side(2)
            # 向下移动抓取
            self.arm.grap(1)
            self.arm.set_offset(0, -0.045)
            time.sleep(0.1)
            self.arm.set_offset(0, 0.045)# 向上移动
            self.arm.set_hand_angle(-130)# 手臂指向方向调整水平
            self.arm.switch_side(1)

        if row==1:
            my_height7=0.02#如果水平就是0
        else:
            my_height7=0.11#水平为0.09
        self.arm.set(0.15,my_height7)
        time.sleep(0.2)
        self.arm.set_hand_angle(-125)
        # 手臂向前伸运动0.14m
        self.arm.set_offset(0.11*self.arm.side, 0, speed=[0.18, 0.06])
        self.arm.grap(0)
        time.sleep(0.1) 
        self.arm.set_offset(-0.02*self.arm.side, 0, speed=[0.18, 0.06])
        self.arm.set_offset(0, 0.05, speed=[0.12, 0.1])
        self.arm.set_offset(-0.09*self.arm.side, 0, speed=[0.18, 0.06])
        
    def mysterious_mission(self):
        self.arm.grap(1)
        self.arm.set(0.15,0.11)
        self.arm.set(0.29,0.11)#伸出
        self.arm.set(0.29,0.071)#下降吸取
        self.arm.set(0.29,0.09)#上升
        self.arm.set(0.21,0.09)#回到位置
        self.arm.set_arm_angle(-110,50)#转向
        time.sleep(0.3)
        self.arm.set(0.21,0.05)#降低
        time.sleep(0.3)
        self.arm.grap(0)#放下
        self.arm.set_hand_angle(-45)
        time.sleep(0.1)
        self.arm.set_hand_angle(15)
