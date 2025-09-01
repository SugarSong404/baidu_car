import os
import json
import shutil
from pathlib import Path
from tqdm import tqdm

dataset_dir = Path(os.path.dirname(__file__)) 
image_dir = dataset_dir / 'images'
anno_dir = dataset_dir / 'annotations'

output_img_dir = dataset_dir / 'images2'
output_lbl_dir = dataset_dir / 'labels'

for split in ['train', 'val']:
    (output_img_dir / split).mkdir(parents=True, exist_ok=True)

def convert_coco_bbox_to_yolo(bbox, img_w, img_h):
    x, y, w, h = bbox
    x_center = (x + w / 2) / img_w
    y_center = (y + h / 2) / img_h
    w /= img_w
    h /= img_h
    return [x_center, y_center, w, h]

def process_json(json_path, split):
    with open(json_path, 'r', encoding='utf-8') as f:
        coco = json.load(f)

    images = {img['id']: img for img in coco['images']}
    annotations = coco['annotations']
    categories = {cat['id']: cat['name'] for cat in coco['categories']}

    img_to_anns = {}
    for ann in annotations:
        img_id = ann['image_id']
        img_to_anns.setdefault(img_id, []).append(ann)

    for img_id, img_info in tqdm(images.items(), desc=f'Processing {split}'):
        file_name = img_info['file_name']
        img_path = image_dir / file_name
        if not img_path.exists():
            print(f"[警告] 图片缺失：{img_path}")
            continue

        dst_img_path = output_img_dir / split / file_name
        if not dst_img_path.exists():
            os.link(img_path, dst_img_path)


process_json(anno_dir / 'instance_train.json', 'train')
process_json(anno_dir / 'instance_val.json', 'val')
