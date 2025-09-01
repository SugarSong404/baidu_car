import socket
import struct
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import io
import time
import queue

import os

CONFIG_FILE = os.path.dirname(__file__)+'/config.txt'

class ClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("百度小车遥控")

        # ===== 新增：IP 与端口输入 =====
        config_frame = tk.Frame(root)
        config_frame.pack(pady=5)

        tk.Label(config_frame, text="IP:").grid(row=0, column=0)
        self.entry_ip = tk.Entry(config_frame, width=15)
        self.entry_ip.insert(0, '192.168.192.112')
        self.entry_ip.grid(row=0, column=1)

        tk.Label(config_frame, text="视频端口:").grid(row=0, column=2)
        self.entry_port_video = tk.Entry(config_frame, width=6)
        self.entry_port_video.insert(0, '9517')
        self.entry_port_video.grid(row=0, column=3)

        tk.Label(config_frame, text="控制端口:").grid(row=0, column=4)
        self.entry_port_control = tk.Entry(config_frame, width=6)
        self.entry_port_control.insert(0, '9827')
        self.entry_port_control.grid(row=0, column=5)

        self.btn_connect = tk.Button(config_frame, text="连接服务器", command=self.connect)
        self.btn_connect.grid(row=0, column=6, padx=5)

        self.video_label = tk.Label(root)
        self.video_label.pack()

        control_frame = tk.Frame(root)
        control_frame.pack(pady=5)

        self.btn_start = tk.Button(control_frame, text="开始录屏", command=self.start_record)
        self.btn_start.grid(row=0, column=0, padx=5)
        self.btn_stop = tk.Button(control_frame, text="停止录屏", command=self.stop_record)
        self.btn_stop.grid(row=0, column=1, padx=5)

        self.btn_refresh = tk.Button(control_frame, text="刷新列表", command=self.refresh_record_list)
        self.btn_refresh.grid(row=0, column=2, padx=5)

        # ===== 新增：删除文件按钮 =====
        self.btn_delete = tk.Button(control_frame, text="删除选中文件", command=self.delete_selected)
        self.btn_delete.grid(row=0, column=3, padx=5)

        self.record_list = ttk.Treeview(root, columns=("filename",), show='headings')
        self.record_list.heading('filename', text='录屏文件')
        self.record_list.pack(fill='both', expand=True)
        self.record_list.bind('<Double-1>', self.download_selected)

        self.video_sock = None
        self.control_sock = None

        self.running = True
        self.frame_queue = queue.Queue(maxsize=10)
        self.pressed_keys = set()

        self.load_config()
        self.root.bind('<KeyPress>', self.on_key_press)
        self.root.bind('<KeyRelease>', self.on_key_release)

    def save_config(self, ip, port_video, port_control):
        try:
            with open(CONFIG_FILE, 'w') as f:
                f.write(f"{ip},{port_video},{port_control}")
        except Exception as e:
            print("配置保存失败:", e)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    ip, port_video, port_control = f.read().strip().split(',')
                    self.entry_ip.delete(0, tk.END)
                    self.entry_ip.insert(0, ip)
                    self.entry_port_video.delete(0, tk.END)
                    self.entry_port_video.insert(0, port_video)
                    self.entry_port_control.delete(0, tk.END)
                    self.entry_port_control.insert(0, port_control)
            except Exception as e:
                print("配置读取失败:", e)

    def connect(self):
        ip = self.entry_ip.get()
        port_video = int(self.entry_port_video.get())
        port_control = int(self.entry_port_control.get())

        try:
            self.video_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.video_sock.connect((ip, port_video))

            self.control_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.control_sock.connect((ip, port_control))

            threading.Thread(target=self.video_loop, daemon=True).start()
            self.start_video_update()

            self.save_config(ip, port_video, port_control)
            self.root.focus_set() 

            messagebox.showinfo("连接成功", f"已连接到 {ip}")
        except Exception as e:
            messagebox.showerror("连接失败", f"无法连接服务器: {e}")


    def start_video_update(self):
        try:
            frame_data = None
            while not self.frame_queue.empty():
                frame_data = self.frame_queue.get_nowait()
            if frame_data:
                image = Image.open(io.BytesIO(frame_data))
                imgtk = ImageTk.PhotoImage(image=image)
                self.video_label.imgtk = imgtk
                self.video_label.config(image=imgtk)
        except Exception as e:
            print('视频显示错误:', e)
        if self.running:
            self.root.after(30, self.start_video_update)

    def video_loop(self):
        data_buffer = b''
        payload_size = 4
        while self.running:
            try:
                while len(data_buffer) < payload_size:
                    data_buffer += self.video_sock.recv(4096)
                packed_msg_size = data_buffer[:payload_size]
                data_buffer = data_buffer[payload_size:]
                msg_size = struct.unpack('>I', packed_msg_size)[0]

                while len(data_buffer) < msg_size:
                    data_buffer += self.video_sock.recv(4096)
                frame_data = data_buffer[:msg_size]
                data_buffer = data_buffer[msg_size:]

                if self.frame_queue.full():
                    try:
                        self.frame_queue.get_nowait()
                    except queue.Empty:
                        pass
                self.frame_queue.put(frame_data)
            except Exception as e:
                print('视频接收错误:', e)
                break

    def send_control(self, msg):
        try:
            self.control_sock.sendall(msg.encode())
        except Exception as e:
            print('控制消息发送失败:', e)

    def start_record(self):
        self.send_control('START_RECORD')

    def stop_record(self):
        self.send_control('STOP_RECORD')

    def refresh_record_list(self):
        self.send_control('GET_RECORD_LIST')
        try:
            data = self.control_sock.recv(4096).decode()
            files = data.split('|') if data else []
            for i in self.record_list.get_children():
                self.record_list.delete(i)
            for f in files:
                if f:
                    self.record_list.insert('', 'end', values=(f,))
        except Exception as e:
            messagebox.showerror("错误", f"获取录屏列表失败: {e}")

    def delete_selected(self):
        item = self.record_list.selection()
        if not item:
            return
        filename = self.record_list.item(item[0])['values'][0]
        if messagebox.askyesno("确认删除", f"确定要删除文件：{filename}？"):
            self.send_control(f'DELETE:{filename}')
            time.sleep(0.5)
            self.refresh_record_list()

    def download_selected(self, event):
        item = self.record_list.selection()
        if not item:
            return
        filename = self.record_list.item(item[0])['values'][0]
        self.send_control(f'DOWNLOAD:{filename}')
        try:
            raw_size = self.control_sock.recv(8)
            filesize = struct.unpack('>Q', raw_size)[0]
            if filesize == 0:
                messagebox.showerror("错误", "文件不存在或无法下载")
                return
        except Exception as e:
            messagebox.showerror("错误", f"获取文件大小失败: {e}")
            return

        save_path = filedialog.asksaveasfilename(initialfile=filename)
        if not save_path:
            return

        try:
            with open(save_path, 'wb') as f:
                remaining = filesize
                while remaining > 0:
                    chunk_size = 4096 if remaining > 4096 else remaining
                    chunk = self.control_sock.recv(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    remaining -= len(chunk)
            messagebox.showinfo("完成", f"{filename} 下载完成")
        except Exception as e:
            messagebox.showerror("错误", f"保存文件失败: {e}")

    def on_key_press(self, event):
        key = event.keysym.upper()
        if key in ['W', 'A', 'S', 'D', 'I', 'K'] and key not in self.pressed_keys:
            self.pressed_keys.add(key)
            self.send_control(f'{key}-PRESS')

    def on_key_release(self, event):
        key = event.keysym.upper()
        if key in self.pressed_keys:
            self.pressed_keys.remove(key)
            self.send_control(f'{key}-RELEASE')

    def on_close(self):
        self.running = False
        try:
            if self.video_sock:
                self.video_sock.close()
            if self.control_sock:
                self.control_sock.close()
        except:
            pass
        self.root.destroy()

if __name__ == '__main__':
    root = tk.Tk()
    app = ClientApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
