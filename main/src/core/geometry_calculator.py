import math
import numpy as np
from src.config.config import Config


class GeometryCalculator:
    def __init__(self):
        self.measurements = {}
        self.measurement_history = []  # 测量历史，用于多帧平均
        self.precision = Config.MEASUREMENT_PRECISION  # 精度设置
        self.stable_measurements = {}  # 稳定后的测量结果
        self.stable_count = 0  # 稳定计数
    
    def calculate_shoulder_width(self, left_shoulder, right_shoulder, scale_factor, frame_width, frame_height):
        """直接测量：肩宽（正面水平距离）"""
        dx = (left_shoulder.x - right_shoulder.x) * frame_width
        dy = (left_shoulder.y - right_shoulder.y) * frame_height
        pixel_distance = math.sqrt(dx ** 2 + dy ** 2)
        return pixel_distance * scale_factor
    
    def calculate_hip_width(self, left_hip, right_hip, scale_factor, frame_width, frame_height):
        """直接测量：臀宽（正面水平距离）"""
        dx = (left_hip.x - right_hip.x) * frame_width
        dy = (left_hip.y - right_hip.y) * frame_height
        return math.sqrt(dx ** 2 + dy ** 2) * scale_factor
    
    def calculate_distance_3d(self, point1, point2, scale_factor, frame_width, frame_height):
        """直接测量：基于关键点的 3D 欧氏距离"""
        dx = (point1.x - point2.x) * frame_width
        dy = (point1.y - point2.y) * frame_height
        dz = (point1.z - point2.z) * frame_width * Config.DEPTH_SCALE_FACTOR
        return math.sqrt(dx ** 2 + dy ** 2 + dz ** 2) * scale_factor
    
    def calculate_arm_length(self, shoulder, elbow, wrist, scale_factor, frame_width, frame_height):
        """直接测量：臂长（上臂 + 前臂）"""
        upper_arm = self.calculate_distance_3d(shoulder, elbow, scale_factor, frame_width, frame_height)
        forearm = self.calculate_distance_3d(elbow, wrist, scale_factor, frame_width, frame_height)
        return upper_arm + forearm
    
    def calculate_forearm_length(self, elbow, wrist, scale_factor, frame_width, frame_height):
        """直接测量：前臂长度"""
        return self.calculate_distance_3d(elbow, wrist, scale_factor, frame_width, frame_height)
    
    def calculate_upper_arm_length(self, shoulder, elbow, scale_factor, frame_width, frame_height):
        """直接测量：上臂长度"""
        return self.calculate_distance_3d(shoulder, elbow, scale_factor, frame_width, frame_height)
    
    def calculate_leg_length(self, hip, knee, ankle, scale_factor, frame_width, frame_height):
        """直接测量：腿长（大腿 + 小腿）"""
        thigh = self.calculate_distance_3d(hip, knee, scale_factor, frame_width, frame_height)
        calf = self.calculate_distance_3d(knee, ankle, scale_factor, frame_width, frame_height)
        return thigh + calf
    
    def calculate_thigh_length(self, hip, knee, scale_factor, frame_width, frame_height):
        """直接测量：大腿长度"""
        return self.calculate_distance_3d(hip, knee, scale_factor, frame_width, frame_height)
    
    def calculate_calf_length(self, knee, ankle, scale_factor, frame_width, frame_height):
        """直接测量：小腿长度"""
        return self.calculate_distance_3d(knee, ankle, scale_factor, frame_width, frame_height)
    
    def calculate_height(self, landmarks, scale_factor, frame_width, frame_height):
        """
        身高估算（估算项）
        
        原理：从鼻尖到双脚踝中点的垂直距离
        校正：由于使用鼻尖而非头顶，需要乘以校正因子
        
        修复说明：
        - 正确使用左右脚踝的 y 坐标平均值
        - 不再使用过大的校正因子（原 1.08 改为 1.0）
        - 从鼻尖到头顶的额外高度已通过 HEIGHT_CORRECTION_FACTOR 考虑
        """
        nose = landmarks[0]
        left_ankle = landmarks[27]
        right_ankle = landmarks[28]
        
        # 修复：正确计算双脚踝的平均 y 坐标
        left_ankle_y = left_ankle.y * frame_height
        right_ankle_y = right_ankle.y * frame_height
        average_ankle_y = (left_ankle_y + right_ankle_y) / 2.0
        
        nose_y = nose.y * frame_height
        vertical_distance = max(0, average_ankle_y - nose_y)
        
        # 身高 = 垂直距离 × 比例系数 × 身高校正因子
        # 校正因子考虑了从鼻尖到头顶的额外高度
        height_cm = vertical_distance * scale_factor * Config.HEIGHT_CORRECTION_FACTOR
        return height_cm
    
    def calculate_waist_width(self, landmarks, scale_factor, frame_width, frame_height):
        """经验估算：腰宽"""
        left_shoulder = landmarks[11]
        right_shoulder = landmarks[12]
        
        shoulder_width = self.calculate_shoulder_width(
            left_shoulder, right_shoulder, scale_factor, frame_width, frame_height
        )
        waist_width = shoulder_width * Config.WAIST_WIDTH_FROM_SHOULDER_RATIO
        return waist_width
    
    def calculate_neck_circumference(self, landmarks, scale_factor, frame_width, frame_height):
        """经验估算：颈围"""
        left_shoulder = landmarks[11]
        right_shoulder = landmarks[12]
        shoulder_width = self.calculate_shoulder_width(
            left_shoulder, right_shoulder, scale_factor, frame_width, frame_height
        )
        neck_width = shoulder_width * Config.NECK_WIDTH_RATIO
        return neck_width * Config.NECK_CIRCUMFERENCE_FACTOR
    
    def estimate_waist_circumference(self, landmarks, scale_factor, frame_width, frame_height):
        """经验估算：腰围"""
        left_shoulder = landmarks[11]
        right_shoulder = landmarks[12]
        shoulder_width = self.calculate_shoulder_width(
            left_shoulder, right_shoulder, scale_factor, frame_width, frame_height
        )
        waist_width = shoulder_width * Config.WAIST_WIDTH_RATIO
        return waist_width * Config.WAIST_CIRCUMFERENCE_FACTOR
    
    def estimate_hip_circumference(self, landmarks, scale_factor, frame_width, frame_height):
        """经验估算：臀围"""
        left_hip = landmarks[23]
        right_hip = landmarks[24]
        hip_width = self.calculate_hip_width(left_hip, right_hip, scale_factor, frame_width, frame_height)
        return hip_width * Config.HIP_CIRCUMFERENCE_FACTOR
    
    def estimate_chest_circumference(self, landmarks, scale_factor, frame_width, frame_height):
        """经验估算：胸围"""
        left_shoulder = landmarks[11]
        right_shoulder = landmarks[12]
        shoulder_width = self.calculate_shoulder_width(
            left_shoulder, right_shoulder, scale_factor, frame_width, frame_height
        )
        chest_width = shoulder_width * Config.CHEST_WIDTH_RATIO
        return chest_width * Config.CHEST_CIRCUMFERENCE_ELLIPSE_FACTOR
    
    def calculate_all_measurements(self, landmarks, scale_factor, frame_width, frame_height):
        """计算所有测量数据，兼容旧接口，并在结构上区分直接测量项与经验估算项"""
        self.measurements = {}
        
        # ========== 直接测量项 ==========
        shoulder_width = self.calculate_shoulder_width(
            landmarks[11], landmarks[12], scale_factor, frame_width, frame_height
        )
        self.measurements["shoulder"] = round(shoulder_width, self.precision)
        
        height = self.calculate_height(
            landmarks, scale_factor, frame_width, frame_height
        )
        self.measurements["height"] = round(height, self.precision)
        
        left_arm_length = self.calculate_arm_length(
            landmarks[11], landmarks[13], landmarks[15], scale_factor, frame_width, frame_height
        )
        self.measurements["arm_left"] = round(left_arm_length, self.precision)
        
        right_arm_length = self.calculate_arm_length(
            landmarks[12], landmarks[14], landmarks[16], scale_factor, frame_width, frame_height
        )
        self.measurements["arm_right"] = round(right_arm_length, self.precision)
        
        left_upper_arm = self.calculate_upper_arm_length(
            landmarks[11], landmarks[13], scale_factor, frame_width, frame_height
        )
        self.measurements["upper_arm_left"] = round(left_upper_arm, self.precision)
        
        left_forearm = self.calculate_forearm_length(
            landmarks[13], landmarks[15], scale_factor, frame_width, frame_height
        )
        self.measurements["forearm_left"] = round(left_forearm, self.precision)
        
        right_upper_arm = self.calculate_upper_arm_length(
            landmarks[12], landmarks[14], scale_factor, frame_width, frame_height
        )
        self.measurements["upper_arm_right"] = round(right_upper_arm, self.precision)
        
        right_forearm = self.calculate_forearm_length(
            landmarks[14], landmarks[16], scale_factor, frame_width, frame_height
        )
        self.measurements["forearm_right"] = round(right_forearm, self.precision)
        
        left_leg_length = self.calculate_leg_length(
            landmarks[23], landmarks[25], landmarks[27], scale_factor, frame_width, frame_height
        )
        self.measurements["leg_left"] = round(left_leg_length, self.precision)
        
        right_leg_length = self.calculate_leg_length(
            landmarks[24], landmarks[26], landmarks[28], scale_factor, frame_width, frame_height
        )
        self.measurements["leg_right"] = round(right_leg_length, self.precision)
        
        left_thigh = self.calculate_thigh_length(
            landmarks[23], landmarks[25], scale_factor, frame_width, frame_height
        )
        self.measurements["thigh_left"] = round(left_thigh, self.precision)
        
        left_calf = self.calculate_calf_length(
            landmarks[25], landmarks[27], scale_factor, frame_width, frame_height
        )
        self.measurements["calf_left"] = round(left_calf, self.precision)
        
        right_thigh = self.calculate_thigh_length(
            landmarks[24], landmarks[26], scale_factor, frame_width, frame_height
        )
        self.measurements["thigh_right"] = round(right_thigh, self.precision)
        
        right_calf = self.calculate_calf_length(
            landmarks[26], landmarks[28], scale_factor, frame_width, frame_height
        )
        self.measurements["calf_right"] = round(right_calf, self.precision)
        
        hip_width = self.calculate_hip_width(
            landmarks[23], landmarks[24], scale_factor, frame_width, frame_height
        )
        self.measurements["hip_width"] = round(hip_width, self.precision)
        
        # ========== 经验估算项 ==========
        waist_width = self.calculate_waist_width(
            landmarks, scale_factor, frame_width, frame_height
        )
        self.measurements["waist_width"] = round(waist_width, self.precision)
        
        chest_circumference = self.estimate_chest_circumference(
            landmarks, scale_factor, frame_width, frame_height
        )
        self.measurements["chest"] = round(chest_circumference, self.precision)
        
        waist_circumference = self.estimate_waist_circumference(
            landmarks, scale_factor, frame_width, frame_height
        )
        self.measurements["waist"] = round(waist_circumference, self.precision)
        
        hip_circumference = self.estimate_hip_circumference(
            landmarks, scale_factor, frame_width, frame_height
        )
        self.measurements["hip"] = round(hip_circumference, self.precision)
        
        neck_circumference = self.calculate_neck_circumference(
            landmarks, scale_factor, frame_width, frame_height
        )
        self.measurements["neck"] = round(neck_circumference, self.precision)
        
        # 额外保留分组结构，供上层展示时按类别读取；旧调用仍可继续直接读取平铺字段
        self.measurements["direct_measurements"] = {
            "height": self.measurements["height"],
            "shoulder": self.measurements["shoulder"],
            "arm_left": self.measurements["arm_left"],
            "arm_right": self.measurements["arm_right"],
            "upper_arm_left": self.measurements["upper_arm_left"],
            "upper_arm_right": self.measurements["upper_arm_right"],
            "forearm_left": self.measurements["forearm_left"],
            "forearm_right": self.measurements["forearm_right"],
            "leg_left": self.measurements["leg_left"],
            "leg_right": self.measurements["leg_right"],
            "thigh_left": self.measurements["thigh_left"],
            "thigh_right": self.measurements["thigh_right"],
            "calf_left": self.measurements["calf_left"],
            "calf_right": self.measurements["calf_right"],
            "hip_width": self.measurements["hip_width"]
        }
        self.measurements["estimated_measurements"] = {
            "waist_width": self.measurements["waist_width"],
            "chest": self.measurements["chest"],
            "waist": self.measurements["waist"],
            "hip": self.measurements["hip"],
            "neck": self.measurements["neck"]
        }
        
        if Config.ENABLE_MULTI_FRAME_AVERAGE:
            history_item = {}
            for key, value in self.measurements.items():
                if not isinstance(value, dict):
                    history_item[key] = value
            self.measurement_history.append(history_item)
            if len(self.measurement_history) > Config.MULTI_FRAME_COUNT:
                self.measurement_history.pop(0)
        
        return self.measurements
    
    def get_averaged_measurements(self):
        """获取多帧平均测量结果"""
        if not self.measurement_history:
            return self.measurements
        
        averaged = {}
        numeric_keys = [key for key, value in self.measurements.items() if not isinstance(value, dict)]
        for key in numeric_keys:
            values = [m.get(key, 0) for m in self.measurement_history]
            averaged[key] = round(sum(values) / len(values), self.precision)
        
        if "direct_measurements" in self.measurements:
            averaged["direct_measurements"] = {
                key: averaged.get(key, value)
                for key, value in self.measurements["direct_measurements"].items()
            }
        
        if "estimated_measurements" in self.measurements:
            averaged["estimated_measurements"] = {
                key: averaged.get(key, value)
                for key, value in self.measurements["estimated_measurements"].items()
            }
        
        return averaged
    
    def get_measurements(self):
        return self.measurements
    
    def reset(self):
        self.measurements = {}
        self.measurement_history = []