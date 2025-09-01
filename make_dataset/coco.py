# coco2yolo.py
import os
import json
from pathlib import Path
from tqdm import tqdm

def convert_coco_json(json_path, save_dir):
    with open(json_path, 'r', encoding='utf-8') as f:
        coco = json.load(f)

    categories = {cat['id']: i for i, cat in enumerate(coco['categories'])}
    image_map = {img['id']: img for img in coco['images']}

    os.makedirs(save_dir, exist_ok=True)

    # 逐图像写标签文件
    labels = {img['id']: [] for img in coco['images']}
    for ann in coco['annotations']:
        img_id = ann['image_id']
        x, y, w, h = ann['bbox']
        img = image_map[img_id]
        dw = 1. / img['width']
        dh = 1. / img['height']
        x_center = (x + w / 2) * dw
        y_center = (y + h / 2) * dh
        w *= dw
        h *= dh

        cls_id = categories[ann['category_id']]
        labels[img_id].append(f"{cls_id} {x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f}")

    for img_id, anns in tqdm(labels.items()):
        img = image_map[img_id]
        img_name = Path(img['file_name']).stem
        label_path = os.path.join(save_dir, f"{img_name}.txt")
        with open(label_path, 'w') as f:
            f.write('\n'.join(anns))

    print(f"✅ 转换完成，共 {len(labels)} 个标签文件保存在: {save_dir}")


if __name__ == "__main__":
    p = os.path.dirname(__file__)
    convert_coco_json(p + "/annotations/instance_train.json", p + "/labels/train")
    convert_coco_json(p + "/annotations/instance_val.json", p + "/labels/val")
