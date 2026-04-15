import cv2
import time
import numpy as np

class VideoCapture:
    def __init__(self, camera_id=0):
        self.camera_id = camera_id
        self.cap = None
    
    def open(self):
        # Windows 优先使用 DirectShow 后端
        self.cap = cv2.VideoCapture(self.camera_id, cv2.CAP_DSHOW)
        
        if not self.cap.isOpened():
            # 如果 DirectShow 失败，尝试自动选择
            self.cap = cv2.VideoCapture(self.camera_id)
        
        if not self.cap.isOpened():
            raise Exception(f"无法打开摄像头 {self.camera_id}")
        
        # 设置缓冲区大小
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # 等待摄像头初始化
        time.sleep(1.0)
        
        # 读取几帧让摄像头稳定
        for _ in range(10):
            self.cap.read()
        
        return True
    
    def read(self):
        if self.cap is None:
            raise Exception("摄像头未打开")
        
        # 尝试读取，失败时重试
        for i in range(10):
            ret, frame = self.cap.read()
            if ret and frame is not None and frame.size > 0:
                return frame
            # 不等待，直接重试
            self.cap.grab()  # 预读取
        
        # 如果多次失败，返回一个黑色帧而不是抛出异常
        print("Warning: Failed to read frame, returning black frame")
        return np.zeros((480, 640, 3), dtype=np.uint8)
    
    def release(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
    
    def is_opened(self):
        return self.cap is not None and self.cap.isOpened()
    
    def set_property(self, prop_id, value):
        if self.cap is not None:
            self.cap.set(prop_id, value)
    
    def get_property(self, prop_id):
        if self.cap is not None:
            return self.cap.get(prop_id)
        return None