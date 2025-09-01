import sys
import os, time
import numpy as np
import requests
import base64
import cv2
from Ts_code import ts_init
ts_init.init_env(os.path.dirname(__file__) + "/paddle_jetson/PaddleOCR")
from predict_system import TextSystem
from predict_system import utility
import logging
logging.disable(logging.DEBUG)
logging.disable(logging.WARNING)


def calculate_area(coordinates):
    x_coords = [point[0] for point in coordinates]
    y_coords = [point[1] for point in coordinates]
    length = max(x_coords) - min(x_coords)
    width = max(y_coords) - min(y_coords)
    area = length * width
    return area

def compute_box_center(box):
    x_min = min(point[0] for point in box)
    x_max = max(point[0] for point in box)
    y_min = min(point[1] for point in box)
    y_max = max(point[1] for point in box)
    return ((x_min + x_max) / 2, (y_min + y_max) / 2)

def simple_cluster_texts(data, y_thresh=70.0, x_thresh=100.0):
    if not data:return []
    data_sorted = sorted(data, key=lambda item: item[0][1])
    lines = []
    current_line = [data_sorted[0]]
    for i in range(1, len(data_sorted)):
        (_, y1), _ = data_sorted[i-1]
        (_, y2), _ = data_sorted[i]
        if abs(y2 - y1) <= y_thresh:
            current_line.append(data_sorted[i])
        else:
            lines.append(current_line)
            current_line = [data_sorted[i]]
    lines.append(current_line)
    results = []
    for line in lines:
        line_sorted = sorted(line, key=lambda item: item[0][0])
        segment = [line_sorted[0]]
        for i in range(1, len(line_sorted)):
            (x1, _), _ = line_sorted[i-1]
            (x2, _), _ = line_sorted[i]
            if abs(x2 - x1) <= x_thresh:
                segment.append(line_sorted[i])
            else:
                results.append(segment)
                segment = [line_sorted[i]]
        results.append(segment)
    return results

def join_clusters_by_y(clusters):
    results = []
    for cluster in clusters:
        cluster_sorted = sorted(cluster, key=lambda item: item[0][1])
        combined_text = ''.join(text for _, text in cluster_sorted)
        results.append(combined_text)
    return results

class Ocr():
    def __init__(self, model_path = os.path.dirname(__file__) + "/my_models/ocr"):
        sys.argv = [
            '',
            f"--det_model_dir={model_path}/det/",
            f"--rec_model_dir={model_path}/rec/",
            f"--rec_char_dict_path={model_path}/rec/dict.txt",
            "--use_gpu=True",
        ]
        args = utility.parse_args()
        args.image_dir = None
        self.text_sys = TextSystem(args)

        print("模型 ocr 已经完成初始化", flush = True)

    def predict(self, img, pre = 0.98):
        dt_boxes, rec_res, _ = self.text_sys(img)
        results = []
        if dt_boxes is not None and rec_res is not None:
            for box, (text, score) in zip(dt_boxes, rec_res):
                area = calculate_area(box)
                if score > pre or (score > pre - 0.08 and area > 500):
                    results.append((compute_box_center(box), text))
        if len(results) == 0: return []
        return results

    def predict_det(self, img):
        dt_boxes, elapse = self.text_sys.text_detector(img)
        return dt_boxes

    def predict_lines(self, img, pre = 0.98):
        results = self.predict(img, pre)
        lines = join_clusters_by_y(simple_cluster_texts(results))
        return lines