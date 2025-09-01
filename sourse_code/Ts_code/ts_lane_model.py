import os
import random
import paddle
import paddle.nn as nn
import paddle.vision.transforms as T
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
from paddle.vision.models import resnet18
import cv2

class LaneReg:
    def __init__(self, name, model_path = None):
        if model_path is None:
            model_path = os.path.dirname(__file__) + f"/my_models/lane/{name}.pdparams"

        class LaneRegressor(nn.Layer):
            def __init__(self):
                super().__init__()
                self.backbone = resnet18(pretrained=False)
                self.backbone.fc = nn.Sequential(
                    nn.Linear(512, 256),
                    nn.ReLU(),
                    nn.Dropout(0.3),
                    nn.Linear(256, 1)
                )

            def forward(self, x):
                return self.backbone(x)

        self.model = LaneRegressor()
        self.model.set_state_dict(paddle.load(model_path))
        self.model.eval()

        self.transform = T.Compose([
            T.Resize((384, 512)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406],
                        std=[0.229, 0.224, 0.225])
        ])
    
        print(f"模型 lane-{name} 已经完成初始化", flush = True)

    def predict(self, img_bgr):
        if isinstance(img_bgr, np.ndarray):img_rgb = Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
        elif isinstance(img_bgr, Image.Image):img_rgb = img_bgr.convert('RGB')
        else:raise TypeError("img_bgr type error")

        input_tensor = self.transform(img_rgb).unsqueeze(0)
        with paddle.no_grad():
            pred = self.model(input_tensor).numpy()[0][0]
        return float(pred)