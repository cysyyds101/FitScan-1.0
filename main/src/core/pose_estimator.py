import mediapipe as mp
import cv2
import numpy as np
from collections import deque
from src.config.config import Config

class PoseEstimator:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        # 优化：使用更轻量的配置
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=Config.POSE_MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=Config.POSE_MIN_TRACKING_CONFIDENCE,
            model_complexity=0,  # 使用最轻量模型
            enable_segmentation=False,  # 禁用分割提高性能
            smooth_landmarks=True,      # 启用平滑
            static_image_mode=False     # 使用视频模式提高性能
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.prev_landmarks = []
        self.filter_window = min(Config.FILTER_WINDOW_SIZE, 4)  # 限制窗口大小
        self.confidence_history = deque(maxlen=10)
        self.landmarks_buffer = deque(maxlen=min(Config.MULTI_FRAME_COUNT, 5))
        self.frame_count = 0
        self.skip_frames = 0
        self.skip_interval = 2  # 每 3 帧处理 1 帧（降低 GPU 负载）
        self.last_results = None  # 缓存上一帧结果
    
    def process(self, frame):
        # 跳帧处理，降低 GPU 负载
        self.frame_count += 1
        if self.frame_count % self.skip_interval != 0:
            # 返回缓存的结果
            class FakeResults:
                pose_landmarks = self.last_results.pose_landmarks if self.last_results else None
            return FakeResults()
        
        # 缩小帧尺寸处理（降低 GPU 显存占用）
        h, w = frame.shape[:2]
        if h > 480 or w > 640:
            scale = min(480 / h, 640 / w)
            new_w, new_h = int(w * scale), int(h * scale)
            small_frame = cv2.resize(frame, (new_w, new_h))
            rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        else:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        results = self.pose.process(rgb_frame)
        
        # 缓存结果
        if results.pose_landmarks:
            self.last_results = results
        
        return results
    
    def apply_filter(self, landmarks):
        """应用增强的滤波算法以提高稳定性和精度"""
        # 使用指数移动平均 (EMA) 滤波
        if Config.ENABLE_SMOOTHING and len(self.prev_landmarks) > 0:
            alpha = Config.SMOOTHING_FACTOR
            filtered_landmarks = []
            
            for i in range(len(landmarks)):
                if i < len(self.prev_landmarks[-1]):
                    prev = self.prev_landmarks[-1][i]
                    # EMA 滤波：新值 = alpha * 当前值 + (1-alpha) * 历史值
                    x = alpha * landmarks[i].x + (1 - alpha) * prev.x
                    y = alpha * landmarks[i].y + (1 - alpha) * prev.y
                    z = alpha * landmarks[i].z + (1 - alpha) * prev.z
                    filtered_landmarks.append(type('obj', (object,), {'x': x, 'y': y, 'z': z})())
                else:
                    filtered_landmarks.append(landmarks[i])
            
            self.prev_landmarks.append(filtered_landmarks)
            return filtered_landmarks
        
        # 多帧平均滤波
        elif Config.ENABLE_MULTI_FRAME_AVERAGE:
            self.landmarks_buffer.append(landmarks)
            if len(self.landmarks_buffer) >= Config.MULTI_FRAME_COUNT:
                # 计算多帧平均
                avg_landmarks = []
                for i in range(len(landmarks)):
                    avg_x = sum(lm[i].x for lm in self.landmarks_buffer) / len(self.landmarks_buffer)
                    avg_y = sum(lm[i].y for lm in self.landmarks_buffer) / len(self.landmarks_buffer)
                    avg_z = sum(lm[i].z for lm in self.landmarks_buffer) / len(self.landmarks_buffer)
                    avg_landmarks.append(type('obj', (object,), {'x': avg_x, 'y': avg_y, 'z': avg_z})())
                return avg_landmarks
        
        # 移动平均滤波
        if len(self.prev_landmarks) >= self.filter_window:
            filtered_landmarks = []
            
            for i in range(len(landmarks)):
                weights = [0.1, 0.2, 0.3, 0.4] if len(self.prev_landmarks) >= 4 else [1.0 / len(self.prev_landmarks)] * len(self.prev_landmarks)
                
                x = sum(lm[i].x * w for lm, w in zip(self.prev_landmarks[-len(weights):], weights[-len(landmarks):]))
                y = sum(lm[i].y * w for lm, w in zip(self.prev_landmarks[-len(weights):], weights[-len(landmarks):]))
                z = sum(lm[i].z * w for lm, w in zip(self.prev_landmarks[-len(weights):], weights[-len(landmarks):]))
                
                total_weight = sum(weights[-len(landmarks):])
                filtered_landmarks.append(type('obj', (object,), {'x': x/total_weight, 'y': y/total_weight, 'z': z/total_weight})())
            
            self.prev_landmarks.pop(0)
            self.prev_landmarks.append(filtered_landmarks)
            return filtered_landmarks
        else:
            self.prev_landmarks.append(landmarks)
            return landmarks
    
    def draw_landmarks(self, frame, results):
        if results.pose_landmarks:
            self.mp_draw.draw_landmarks(
                frame, 
                results.pose_landmarks, 
                self.mp_pose.POSE_CONNECTIONS
            )
        return frame
    
    def get_keypoints(self, results):
        if results.pose_landmarks:
            return results.pose_landmarks.landmark
        return None
    
    def get_specific_points(self, landmarks, point_indices):
        if not landmarks:
            return None
        return [landmarks[i] for i in point_indices]
    
    def calculate_distance(self, point1, point2, frame_width, frame_height):
        dx = (point1.x - point2.x) * frame_width
        dy = (point1.y - point2.y) * frame_height
        return np.sqrt(dx**2 + dy**2)
    
    def cleanup(self):
        self.pose.close()