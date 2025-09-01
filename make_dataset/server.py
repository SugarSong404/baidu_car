import socket
import threading
import cv2
import struct
import time
import os
import random
from multiprocessing import Process, Event, Queue
from Ts_code import Det
from ts_car import IdealCar

car = IdealCar()
car.task.arm.reset()
car.task.arm.set(0.15, 0.04)
car.task.arm.switch_side(-1)

# det = Det("mys")

HOST = '0.0.0.0'
PORT_VIDEO = random.randint(9000,10000)
PORT_CONTROL = random.randint(PORT_VIDEO+1,10001)
print(f"PORT_VIDEO = {PORT_VIDEO}\nPORT_CONTROL = {PORT_CONTROL}")
VIDEO_DIR = 'recorded_videos'

if not os.path.exists(VIDEO_DIR):
    os.makedirs(VIDEO_DIR)

def record_video(stop_event: Event, filename: str, frame_queue: Queue):
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = None
    while not stop_event.is_set() or not frame_queue.empty():
        if not frame_queue.empty():
            frame = frame_queue.get()
            if out is None:
                h, w = frame.shape[:2]
                out = cv2.VideoWriter(filename, fourcc, 20.0, (w, h))
            out.write(frame)
        else:
            time.sleep(0.01)
    if out:
        out.release()

class VideoServer:
    def __init__(self):
        self.cap = car.cap_side
        self.lock = threading.Lock() 
        self.record_process = None
        self.record_stop_event = Event()
        self.record_queue = Queue()
        self.is_recording = False

        self.go_running = False
        self.go_thread = None
        self.go_stop_event = Event()

        self.back_running = False
        self.back_thread = None
        self.back_stop_event = Event()

        self.left_running = False
        self.left_thread = None
        self.left_stop_event = Event()

        self.right_running = False
        self.right_thread = None
        self.right_stop_event = Event()

        self.armup_running = False
        self.armup_thread = None
        self.armup_stop_event = Event()

        self.armdown_running = False
        self.armdown_thread = None
        self.armdown_stop_event = Event()

    def _go_loop(self):
        while not self.go_stop_event.is_set():
            #car.task.arm.reset()
            car.set_velocity(0.1,0,0)

    def _back_loop(self):
        while not self.back_stop_event.is_set():
            car.set_velocity(-0.1,0,0)

    def _left_loop(self):
        while not self.left_stop_event.is_set():
            #car.task.arm.set_offset(0,0.005,speed=[0.05,0.05])
            car.set_velocity(0,0,0.5)

    def _right_loop(self):
        while not self.right_stop_event.is_set():
            #car.task.arm.set_offset(0.005,0,speed=[0.05,0.05])
            car.set_velocity(0,0,-0.5)

    def _armup_loop(self):
        while not self.armup_stop_event.is_set():
            car.task.arm.set_offset(0, 0.02, 1)

    def _armdown_loop(self):
        while not self.armdown_stop_event.is_set():
            car.task.arm.set_offset(0, -0.02, 1)


    def start_video_stream(self, conn):
        try:
            while True:
                with self.lock:
                    frame = self.cap.read()
                    # TODO:使用下面那行语句后图像带框
                    # frame = det.predict_visual(frame)
                if frame is None:
                    continue

                encoded, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                data = buffer.tobytes()

                conn.sendall(struct.pack('>I', len(data)) + data)


                if self.is_recording:
                    if not self.record_queue.full():
                        self.record_queue.put(frame)
                time.sleep(0.05) 
        except Exception as e:
            print('视频连接断开:', e)
        finally:
            conn.close()

    def handle_control(self, conn):
        try:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                msg = data.decode()

                if msg == 'START_RECORD':
                    if not self.is_recording:
                        self.start_record()
                        conn.sendall(b'OK')
                    else:
                        conn.sendall(b'ALREADY_RECORDING')
                elif msg == 'STOP_RECORD':
                    if self.is_recording:
                        self.stop_record()
                        conn.sendall(b'OK')
                    else:
                        conn.sendall(b'NOT_RECORDING')
                elif msg == 'GET_RECORD_LIST':
                    files = os.listdir(VIDEO_DIR)

                    conn.sendall('|'.join(files).encode())
                elif msg.startswith('DOWNLOAD:'):
                    filename = msg.split(':',1)[1]
                    filepath = os.path.join(VIDEO_DIR, filename)
                    if os.path.exists(filepath):
                        with open(filepath, 'rb') as f:
                            conn.sendall(struct.pack('>Q', os.path.getsize(filepath)))
                            while True:
                                chunk = f.read(4096)
                                if not chunk:
                                    break
                                conn.sendall(chunk)
                    else:
                        conn.sendall(struct.pack('>Q', 0))
                elif msg.startswith('DELETE:'):
                    filename = msg.split(':', 1)[1]
                    filepath = os.path.join(VIDEO_DIR, filename)
                    if os.path.exists(filepath):
                        try:
                            os.remove(filepath)
                            conn.sendall(b'DELETED')
                        except Exception as e:
                            print('删除失败:', e)
                            conn.sendall(b'DELETE_FAILED')
                    else:
                        conn.sendall(b'NOT_FOUND')
                elif len(msg) >= 3 and (msg.endswith('-PRESS') or msg.endswith('-RELEASE')):
                    key = msg[0]
                    action = msg.split('-')[-1]

                    if key == 'W':
                        if action == 'PRESS':
                            if not self.go_running:
                                self.go_stop_event.clear()
                                self.go_thread = threading.Thread(target=self._go_loop)
                                self.go_thread.start()
                                self.go_running = True
                        elif action == 'RELEASE':
                            if self.go_running:
                                self.go_stop_event.set()
                                self.go_thread.join()
                                self.go_running = False
                    elif key == 'S':
                        if action == 'PRESS':
                            if not self.back_running:
                                self.back_stop_event.clear()
                                self.back_thread = threading.Thread(target=self._back_loop)
                                self.back_thread.start()
                                self.back_running = True
                        elif action == 'RELEASE':
                            if self.back_running:
                                self.back_stop_event.set()
                                self.back_thread.join()
                                self.back_running = False
                    elif key == 'A':
                        if action == 'PRESS':
                            if not self.left_running:
                                self.left_stop_event.clear()
                                self.left_thread = threading.Thread(target=self._left_loop)
                                self.left_thread.start()
                                self.left_running = True
                        elif action == 'RELEASE':
                            if self.left_running:
                                self.left_stop_event.set()
                                self.left_thread.join()
                                self.left_running = False
                    elif key == 'D':
                        if action == 'PRESS':
                            if not self.right_running:
                                self.right_stop_event.clear()
                                self.right_thread = threading.Thread(target=self._right_loop)
                                self.right_thread.start()
                                self.right_running = True
                        elif action == 'RELEASE':
                            if self.right_running:
                                self.right_stop_event.set()
                                self.right_thread.join()
                                self.right_running = False
                    elif key == 'I':
                        if action == 'PRESS':
                            if not self.armup_running:
                                self.armup_stop_event.clear()
                                self.armup_thread = threading.Thread(target=self._armup_loop)
                                self.armup_thread.start()
                                self.armup_running = True
                        elif action == 'RELEASE':
                            if self.armup_running:
                                self.armup_stop_event.set()
                                self.armup_thread.join()
                                self.armup_running = False
                    elif key == 'K':
                        if action == 'PRESS':
                            if not self.armdown_running:
                                self.armdown_stop_event.clear()
                                self.armdown_thread = threading.Thread(target=self._armdown_loop)
                                self.armdown_thread.start()
                                self.armdown_running = True
                        elif action == 'RELEASE':
                            if self.armdown_running:
                                self.armdown_stop_event.set()
                                self.armdown_thread.join()
                                self.armdown_running = False
                    print(key)
                else:
                    print("收到未知指令:", msg)
        except Exception as e:
            print('控制连接断开:', e)
        finally:
            conn.close()

    def start_record(self):
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(VIDEO_DIR, f'record_{timestamp}.avi')
        self.record_stop_event.clear()
        self.record_queue = Queue(maxsize=100)
        self.record_process = Process(target=record_video, args=(self.record_stop_event, filename, self.record_queue))
        self.record_process.start()
        self.is_recording = True
        print('开始录屏:', filename)

    def stop_record(self):
        self.record_stop_event.set()
        self.record_process.join()
        self.is_recording = False
        print('停止录屏')

    def run(self):
        threading.Thread(target=self._video_listener, daemon=True).start()
        threading.Thread(target=self._control_listener, daemon=True).start()
        print("服务器启动，等待连接...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("关闭摄像头和服务...")
            self.cap.release()

    def _video_listener(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((HOST, PORT_VIDEO))
        s.listen(1)
        while True:
            conn, addr = s.accept()
            print('视频连接来自', addr)
            threading.Thread(target=self.start_video_stream, args=(conn,), daemon=True).start()

    def _control_listener(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((HOST, PORT_CONTROL))
        s.listen(1)
        while True:
            conn, addr = s.accept()
            print('控制连接来自', addr)
            threading.Thread(target=self.handle_control, args=(conn,), daemon=True).start()

if __name__ == '__main__':
    server = VideoServer()
    server.run()
