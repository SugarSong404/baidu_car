import json
import yaml
import os

# 读取你的 JSON 文件
with open(os.path.dirname(__file__) + "/annotations/instance_train.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# 提取类别名称
names = [cat["name"] for cat in data["categories"]]

# 生成 YAML 数据
yaml_data = {
    "train": "./images/train",
    "val": "./images/val",
    "nc": len(names),
    "names": names
}

# 保存为 data.yaml
with open(os.path.dirname(__file__) + "/data.yaml", "w", encoding="utf-8") as f:
    yaml.dump(yaml_data, f, allow_unicode=True)

print("✅ 已生成 data.yaml")
