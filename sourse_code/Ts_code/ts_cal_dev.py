import cv2
import os
import json
import time
import numpy as np
from collections import deque

import ctypes
lib = ctypes.CDLL(os.path.dirname(__file__)+'/my_models/lane/search_img.so')
lib.search_img.argtypes = [
    np.ctypeslib.ndpointer(dtype=np.uint8, ndim=3, flags='C_CONTIGUOUS'), 
    np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, flags='C_CONTIGUOUS'), 
    ctypes.c_int,
    ctypes.c_int 
]
lib.search_img.restype = None

resize_size = 120
view_limit = 400
YMAX = 116
YMIN = 3
XMAX = 117
XMIN = 2

class Lane:
    def __init__(self, model_path = os.path.dirname(__file__)+"/my_models/lane"):
        standard_path = model_path + "/standard_binary.jpg"
        perspective_path = model_path + "/perspective.json"
        self.last_dev = 0
        self.ann_status = 0
        self.ann_devs = []
        self.draw_f = False
        self.standard_lr = get_standard(standard_path)
        self.perspective = get_perspective(perspective_path, self.standard_lr)

    def draw_basemap(self, img):
        return get_basemap(img)

    def cal_dev(self, img, kk, bb, ann_f=0):
        self.flip_img = get_basemap(img)[:, :, 0]
        left_scan, right_scan = get_scan_line(self.flip_img)
        left_line, right_line = get_lr_line(self.flip_img, left_scan, right_scan)

        if self.ann_status==0 and ann_f==1:
            self.ann_status = 1
        elif self.ann_status==1 and self.draw_f:
            self.ann_status = 2
        elif self.ann_status==2 and ann_f==2:
            self.ann_status = 3
            self.timer = time.time()
        elif self.ann_status == 3 and (time.time() - self.timer) >= 4:
            self.ann_status = 4

        if self.ann_status==1 or self.ann_status==2:
            right_line = [-1]*119
            temp = deal_annulus(self.flip_img)
            if temp is not None:
                left_line = temp
                self.draw_f = True
        elif self.ann_status==3:
            return sum(self.ann_devs)/len(self.ann_devs)

        struct_lr = [process_line(left_line), process_line(right_line)]
        struct_lr = delete_line(self.flip_img, [left_scan, right_scan], struct_lr)
        dev = calculate_dev(self.standard_lr, struct_lr, self.perspective, [kk, bb])
        if dev is None:dev = self.last_dev

        if self.ann_status==2:
            self.ann_devs.append(dev)

        self.last_dev = dev
        return dev

    def get_order(self):
        if self.ann_status == 0:return 1
        elif self.ann_status <=3:return 2
        elif self.ann_status == 4: return 3 

def delete_line(image, scan_lr, struct_lr):
    if (struct_lr[0][2]!=0 and struct_lr[1][2]!=0) and (abs(scan_lr[1]-scan_lr[0]) < 30) and (image[0][scan_lr[0]] > 128 and image[0][scan_lr[1]] > 128):
        arr_l, start_l, len_l = struct_lr[0]
        arr_r, start_r, len_r = struct_lr[1]
        x_l = arr_l[start_l] - arr_l[start_l+len_l-1]
        k_l = abs(len_l / x_l) if x_l!=0 else float('inf')
        x_r = arr_r[start_r] - arr_r[start_r+len_r-1]
        k_r = abs(len_r / x_r) if x_r!=0 else float('inf')
        if k_l-k_r>0:struct_lr[1] = arr_r, 0, 0
        else: struct_lr[0] = arr_r, 0, 0
    return struct_lr

def get_basemap(image):
    def preprocess(image):
        flip_img = cv2.flip(image, 0)

        gray = cv2.cvtColor(flip_img, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 190, 255, cv2.THRESH_BINARY)
        binary_bgr = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
        cropped_img = binary_bgr[:view_limit, :, :]
        binary_resize = cv2.resize(cropped_img, (resize_size, resize_size), interpolation=cv2.INTER_AREA)
        return binary_resize

    def search_img(image, start_x, start_y):
        basemap = np.ones((119, 119), dtype=np.uint8)
        lib.search_img(image, basemap, start_x, start_y)
        return basemap
        
    def get_start_point(image):
        max_len = 0  
        start_point = -1  
        current_len = 0  
        current_start = -1  

        for X in range(0, 119):
            if image[0][X][0] < 128:
                if current_len == 0:
                    current_start = X
                current_len += 1
            else:
                if current_len > max_len:
                    max_len = current_len
                    start_point = current_start
                current_len = 0

        if current_len > max_len:
            max_len = current_len
            start_point = current_start

        return start_point if max_len > 0 else -1

    image = preprocess(image)
    point = get_start_point(image)
    basemap = search_img(image, point, 0)
    gray_image = np.where(basemap == 0, 0, 255).astype(np.uint8)
    gray_image = cv2.cvtColor(gray_image, cv2.COLOR_GRAY2BGR)
    final_img = cv2.flip(gray_image, 0)
    return final_img

def fix_line_array(arr):
    arr = np.array(arr, dtype=float)
    y_coords = np.arange(len(arr))

    valid_mask = arr != -1
    x_valid = arr[valid_mask]
    y_valid = y_coords[valid_mask]

    k, b = np.polyfit(y_valid, x_valid, deg=1)

    for i in range(len(arr)):
        if arr[i] == -1:
            arr[i] = int(k * i + b)
    return arr


def get_lr_line(image, scan_left, scan_right):
    image = np.asarray(image, dtype=np.uint8)
    H = 119
    W = 119

    left = np.full(H, -1, dtype=np.int32)
    right = np.full(H, -1, dtype=np.int32)

    if scan_left >= 2:
        x_left_range = np.arange(scan_left, 1, -1)
        for i, x in enumerate(x_left_range):
            cond = (image[:, x] < 128) & (image[:, x-1] > 128) & (image[:, x-2] > 128)
            update_mask = (left == -1) & cond
            left[update_mask] = x
    if scan_right <= 116:
        x_right_range = np.arange(scan_right, 117)
        for i, x in enumerate(x_right_range):
            cond = (image[:, x] < 128) & (image[:, x+1] > 128) & (image[:, x+2] > 128)
            update_mask = (right == -1) & cond
            right[update_mask] = x

    return left.tolist(), right.tolist()


def get_standard(path):
    standard = cv2.imread(path)[:, :, 0]
    standard_left, standard_right = get_lr_line(standard, 60 ,60)
    return [fix_line_array(standard_left), fix_line_array(standard_right)]

def get_scan_line(image):
    image = np.asarray(image, dtype=np.uint8)
    h, w = image.shape
    col_y      = image[2:, :]
    col_y_m1   = image[1:-1, :]
    col_y_m2   = image[0:-2, :]
    condition  = (col_y < 128) & (col_y_m1 > 128) & (col_y_m2 > 128)

    first_edge = np.argmax(condition, axis=0) + 2
    has_edge = condition.any(axis=0)
    edge_y = np.where(has_edge, first_edge, h)

    edge_y = np.where((edge_y == h) & (image[0, :] < 128), 2, edge_y)
    min_edge_y = edge_y.min()
    candidates = np.where(edge_y == min_edge_y)[0]
    if len(candidates) > 0:
        scan_left = int(candidates[0])
        scan_right = int(candidates[-1])
    else:
        scan_left, scan_right = 118, 0

    return scan_left, scan_right

def process_line(line, max_gap=10):
    max_len = 0
    max_start = 0
    current_start = None
    current_len = 0
    prev_val = None

    for i, val in enumerate(line):
        if val == -1:
            if current_start is not None:
                if current_len > max_len:
                    max_len = current_len
                    max_start = current_start
                current_start = None
                current_len = 0
                prev_val = None
            continue

        if current_start is None:
            current_start = i
            current_len = 1
            prev_val = val
        else:
            if abs(val - prev_val) > max_gap:
                if current_len > max_len:
                    max_len = current_len
                    max_start = current_start
                current_start = i
                current_len = 1
            else:
                current_len += 1
            prev_val = val
    if current_start is not None and current_len > max_len:
        max_len = current_len
        max_start = current_start
    filled = line.copy()
    prev_val = None
    for i in range(max_start, max_start + max_len):
        if filled[i] != -1:
            prev_val = filled[i]
        elif prev_val is not None:
            filled[i] = prev_val
            
    
    if max_len < 10:return filled, 0, 0
    return filled, max_start, max_len


def deal_noneline(image):
    high_line = [-1] * 119
    num=0
    for x in range(0, 119):
        for y in range(117, 0, -1):
            if image[y+1][x] < 128 and image[y][x] < 128 and image[y-1][x]>128:
                num+=1
                high_line[x] = y
    if num<10:return None
    high_line = list(filter(lambda x: x != -1, high_line))
    x = np.arange(len(high_line))
    slope, _ = np.polyfit(x, high_line, 1) 
    if slope > 0:return -40
    elif slope < -0:return 40
    else:return None

def calculate_dev(standard_lr, struct_lr, pers, kb):
    left_struct = struct_lr[0]
    right_struct = struct_lr[1]
    standard_left = standard_lr[0]
    standard_right = standard_lr[1]
    dev_l = None
    dev_r = None

    if right_struct[2] > 10 :dev_r = get_kb(standard_right, right_struct, pers, kb)
    if left_struct[2] > 10 :dev_l = get_kb(standard_left, left_struct, pers, kb)

    if dev_l is not None and dev_r is not None:return (dev_r + dev_l)/2
    if dev_l is not None: return dev_l
    if dev_r is not None: return dev_r
    return None
        
def get_kb(standard, struct, pers, kb):
    sumx = 0
    sumy = 0
    sumxy = 0
    sumx2 = 0
    n = 0 
    x = 0
    y = 0
    for j in range(struct[1], struct[1] + struct[2]):
        n += 1
        y = (struct[0][j] - standard[j])*pers[1][j]
        x = pers[0][j]
        sumx += x
        sumy += y
        sumxy += x * y
        sumx2 += x * x
    k = (n * sumxy - sumx * sumy) / (n * sumx2 - sumx * sumx)
    b = sumy / n - k * sumx / n
    return k * kb[0] + b * kb[1]

def get_perspective(path, standard_lr):
    with open(path, "r") as f:
        data = json.load(f)
    arr = data["arr"]
    wid = data["wid"]
    arr2 = [0] * 119
    for y in range(0, 119):
        arr2[y] = wid / float(standard_lr[1][y] - standard_lr[0][y] + 1)
    return [arr, arr2]

def deal_annulus(image):
    def has_black_white_black(seq, start, end):
        first_white_index = -1
        for i in range(start, end, -1):
            prev, current = seq[i + 1], seq[i]
            if prev < 128 and current >= 128 and first_white_index == -1:
                first_white_index = i 
            elif first_white_index != -1 and prev >= 128 and current < 128:
                return first_white_index
        return -1 

    def change_line(image, corner):
        left_line = [-1]*119
        k = (corner[0]-108)/(corner[1]-0)
        b = corner[0] - k * corner[1] 
        if k==0: return None
        for y in range(108, corner[0]-1, -1):
            left_line[y] = int((y - b)/k)
        for y in range(corner[0]+1, -1, -1):
            for x in range(117, corner[1], -1):
                if image[y][x+1] <128 and image[y][x] < 128 and image[y][x-1] >128:
                    left_line[y] = x
                    break
        return left_line

    num = 0
    start_y = 0
    for y in range(114,5,-1):
        if abs(int(image[y][118])-int(image[y-1][118])) > 128:
            num+=1
            start_y = y
    if image[114][118] > 128 or num!=1:return None
    num = 0
    corner_y = -1
    corner_x = -1
    for y in range(start_y, 118):
        x = has_black_white_black(image[y], 117, -1)
        if x!=-1:
            num += 1
            corner_x = x
            corner_y = y
        else:break
    if num>=3 and corner_x!=-1:return change_line(image, [corner_y, corner_x])
    else:return None