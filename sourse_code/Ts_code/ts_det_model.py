from Ts_code import ts_init
import os
import gc
import cv2
import paddle
import time
import numpy as np
ts_init.init_env(os.path.dirname(__file__) + "/paddle_jetson/PaddleDetection")
from deploy.python.infer import Detector

class Det():
    def __init__(self, name, status = False, model_path=None):
        if model_path is None:
            model_path = os.path.dirname(__file__) + f"/my_models/{name}"
            self.detector = Detector(
                model_dir= model_path,
                device="GPU",
                run_mode='paddle',  
            )
        self.status = status
        print(f"模型 {name} 已经完成初始化", flush = True)
        
    def set_status(self, status):
        self.status = status

    def close(self):
        self.status = False
        self.detector.predictor.clear_intermediate_tensor()
        self.detector.predictor.try_shrink_memory()
        self.detector = None
        gc.collect()
        paddle.device.cuda.empty_cache() 

    def predict(self, img):
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        result = self.detector.predict_image([img],visual=False)
        det_res = self.detector.filter_box(result, 0.8)
        return det_res

    def predict_area(self, img):
        results = []
        det_res = self.predict(img)
        if det_res is not None:
            boxes = det_res.get('boxes', None)
            if boxes is None or len(boxes)==0:
                return []
            else:
                for res in det_res['boxes']:
                    results.append([int(res[0]), cal_area(res[2:])])
                return results
        else: return []

    def predict_dis(self, img):
        results = []
        det_res = self.predict(img)
        if det_res is not None:
            boxes = det_res.get('boxes', None)
            if boxes is None or len(boxes)==0:
                return []
            else:
                for res in det_res['boxes']:
                    results.append([int(res[0]), abs(480 - res[5])])
                return results
        else: return []

    def predict_precise(self, img, ids = [0], pre = 0.9, dis_tho = [0, float('inf')], area_tho = [0, float('inf')]):
        results = []
        det_res = self.predict(img)
        if det_res is not None:
            boxes = det_res.get('boxes', None)
            if boxes is None or len(boxes)==0:
                return False
            else:
                res = det_res['boxes'][0]
                area = cal_area(res[2:])
                dis = abs(480 - res[5])
                if res[0] in ids and  dis > dis_tho[0] and dis < dis_tho[1] and area > area_tho[0] and area < area_tho[1] and res[1] > pre:return True
                else: return False
        else: return False

    def predict_visual(self, img, score_thresh=0.8):
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        result = self.detector.predict_image([img_rgb], visual=False)
        det_res = self.detector.filter_box(result, score_thresh)
        if det_res is None or 'boxes' not in det_res or len(det_res['boxes']) == 0:return img
        draw_img = img.copy()
        for box in det_res['boxes']:
            cls_id = int(box[0])
            score = box[1]
            x_min, y_min, x_max, y_max = map(int, box[2:6])
            cv2.rectangle(draw_img, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
            cv2.putText(draw_img, f"ID:{cls_id} {score:.2f}", (x_min, y_min - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
        return draw_img



def cal_area(box_arr):
    w = abs(box_arr[0]-box_arr[2])
    h = abs(box_arr[1]-box_arr[3])
    return w*h