# 2025智能车百度组国赛鸿泉今朝队代码开源
python版本3.8 paddlepaddle-gpu==2.4.0
使用前请确保阅读baidu_car\sourse_code\Ts_code\paddle_jetson路径下的readme.md
比赛演示视频可以前往B站看到[https://www.bilibili.com/video/BV1C2Y9z4Egf/?share_source=copy_web&vd_source=4a964519fcc652857ee84b2de8572c53](https://www.bilibili.com/video/BV1C2Y9z4Egf/?share_source=copy_web&vd_source=4a964519fcc652857ee84b2de8572c53)
![bae37d028dcc24cfc68d1e55e12247c.jpg](https://i-blog.csdnimg.cn/img_convert/88e3e58a0366bfc13aef8cf64478d526.jpeg)
# 项目目录结构
├── **BaiduCode**
│   └── 官模的封装好的下位机调用库（我修复了一些 Bug 并修改了代码结构）
│
├── **Ts\_code**
│   ├── 各类模型的初始化与调用库
│   │   ├── `paddle_jetson/`
│   │   │   ├── paddleOCR (version 2.7.1)
│   │   │   ├── paddleDetection (version 2.6.0)
│   │   ├── `my_models/`
│   │   │   └── 各类模型存放位置，这部分由所有队友共同努力完成
│   │   ├── 其它 `.py` 文件
│   │   │   └── 各类模型调用的 API 封装
│   │
│
├── **Ts\_run**
│   ├── 项目的主要运行目录
│   │   ├── `go.py`
│   │   │   └── 赛场上最终运行的文件
│   │   ├── `tasks/`
│   │   │   └── 存放了我写的各种任务处理方式
│
├── **ts\_car.py**
│   └── 我继承了 CarBase，可以通过 car 对象 调用 `BaiduCode` 的一系列接口
│
└── **task\_func.py**
└── **我队友 yyb 的手笔**，包含了所有舵机、丝杠的操作，控制着小车的“机械臂”