import os
import sys
import subprocess

def main():
    root_dir = os.path.dirname(__file__)

    yolov5_dir = os.path.join(root_dir, "yolov5")

    data_yaml = os.path.join(root_dir, "data.yaml")

    epochs = 150
    batch_size = 16
    imgsz = 640
    weights = "yolov5s.pt" 

    train_script = os.path.join(yolov5_dir, "train.py")

    cmd = [
        sys.executable, train_script,
        "--img", str(imgsz),
        "--batch", str(batch_size),
        "--epochs", str(epochs),
        "--data", data_yaml,
        "--weights", weights,
        "--device", "0",
        "--project", os.path.join(root_dir, "runs/det"), 
        "--name", "det"
    ]

    print("Running training with command:")
    print(" ".join(cmd))

    result = subprocess.run(cmd, cwd=yolov5_dir)

    if result.returncode == 0:
        print("训练完成！")
    else:
        print("训练失败，请检查错误信息。")

if __name__ == "__main__":
    main()
