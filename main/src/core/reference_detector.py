import cv2
import numpy as np
from src.config.config import Config


class ReferenceDetector:
    def __init__(self):
        self.reference_objects = Config.REFERENCE_OBJECTS
        self.detected_object = None
        self.scale_factor = None
        self.detected_width_px = None  # 参照物的像素宽度
        self.detected_width_cm = None  # 参照物的真实宽度（cm）
    
    def detect(self, frame):
        # 确保 frame 不为空
        if frame is None or frame.size == 0:
            print("Warning: Empty frame in detect()")
            return False, np.full((480, 640, 3), 128, dtype=np.uint8)
        
        original_frame = frame.copy()
        frame = frame.copy()
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(
            gray,
            (Config.GAUSSIAN_KERNEL_SIZE, Config.GAUSSIAN_KERNEL_SIZE),
            0
        )
        
        thresh = cv2.adaptiveThreshold(
            blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 5
        )
        
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        closing = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        edges = cv2.Canny(closing, Config.CANNY_THRESHOLD1, Config.CANNY_THRESHOLD2)
        
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        best_match = None
        best_score = -1
        
        for contour in contours:
            perimeter = cv2.arcLength(contour, True)
            if perimeter < Config.REFERENCE_MIN_PERIMETER:
                continue
            
            area = cv2.contourArea(contour)
            rect = cv2.minAreaRect(contour)
            (center_x, center_y), (rect_w, rect_h), angle = rect
            
            if rect_w <= 1 or rect_h <= 1:
                continue
            
            # 使用 minAreaRect 的短边和长边
            long_side = max(rect_w, rect_h)
            short_side = min(rect_w, rect_h)
            if short_side <= 0:
                continue
            
            aspect_ratio = long_side / short_side
            rect_area = rect_w * rect_h
            rectangularity = area / rect_area if rect_area > 0 else 0
            
            if rectangularity < Config.REFERENCE_RECTANGULARITY_MIN:
                continue
            
            for obj_name, specs in self.reference_objects.items():
                matched, score, scale_factor, ref_width_px, ref_width_cm = self._match_reference_object(
                    specs,
                    area,
                    long_side,
                    short_side,
                    aspect_ratio
                )
                
                if matched and score > best_score:
                    best_score = score
                    best_match = {
                        "object_name": obj_name,
                        "scale_factor": scale_factor,
                        "rect": rect,
                        "box": cv2.boxPoints(rect).astype(np.int32),
                        "long_side": long_side,
                        "short_side": short_side,
                        "area": area,
                        "aspect_ratio": aspect_ratio,
                        "rectangularity": rectangularity,
                        "center": (int(center_x), int(center_y)),
                        "angle": angle,
                        "ref_width_px": ref_width_px,
                        "ref_width_cm": ref_width_cm
                    }
        
        if best_match and best_score >= Config.REFERENCE_MATCH_MIN_SCORE:
            self.scale_factor = best_match["scale_factor"]
            self.detected_object = best_match["object_name"]
            self.detected_width_px = best_match["ref_width_px"]
            self.detected_width_cm = best_match["ref_width_cm"]
            
            # 获取参照物标签
            ref_label = Config.REFERENCE_OBJECTS.get(self.detected_object, {}).get("label", self.detected_object)
            
            cv2.drawContours(frame, [best_match["box"]], -1, (0, 255, 0), 2)
            cv2.circle(frame, best_match["center"], 4, (0, 255, 0), -1)
            cv2.putText(
                frame,
                f"识别：{ref_label} ({best_match['ref_width_cm']:.1f}cm)",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 0),
                2
            )
            cv2.putText(
                frame,
                f"像素尺寸：{best_match['long_side']:.0f}x{best_match['short_side']:.0f}px",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 255, 0),
                2
            )
            cv2.putText(
                frame,
                f"比例系数 K = {self.scale_factor:.4f} cm/px",
                (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )
            
            return True, frame
        
        self.detected_object = None
        self.scale_factor = None
        self.detected_width_px = None
        self.detected_width_cm = None
        
        cv2.putText(frame, "正在检测参照物...", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 150, 255), 2)
        cv2.putText(frame, "请手持 A4 纸/银行卡贴近胸前", (10, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 150, 255), 2)
        
        return False, original_frame
    
    def _match_reference_object(self, specs, area, long_side, short_side, aspect_ratio):
        """
        匹配参照物并计算比例系数。
        
        关键改进：
        - 使用短边（short_side）作为参照物宽度的像素值
        - 根据参照物类型的标准宽度计算 K 值
        """
        object_width = specs.get("width", 0)  # 标准宽度（短边）
        object_height = specs.get("height", object_width)  # 标准高度（长边）
        object_long = max(object_width, object_height)
        object_short = min(object_width, object_height)
        object_aspect = object_long / object_short if object_short > 0 else 0
        
        score = 0.0
        
        # 面积匹配
        if specs["min_area"] * 0.1 < area < specs["max_area"] * 5:
            score += 2.0
        
        # 像素尺寸匹配
        if specs["min_pixel"] * 0.1 < short_side < specs["max_pixel"] * 5:
            score += 2.0
        
        # 长宽比匹配
        aspect_diff = abs(aspect_ratio - object_aspect)
        if aspect_diff <= Config.REFERENCE_ASPECT_TOLERANCE:
            score += max(0.0, 4.0 - aspect_diff * 10.0)
        else:
            return False, score, None, None, None
        
        # 关键修复：使用短边作为参照物宽度的像素值
        # K = 真实宽度 / 像素宽度
        ref_width_px = short_side  # 使用短边作为宽度
        ref_width_cm = object_short  # 使用标准短边宽度
        scale_factor = ref_width_cm / ref_width_px if ref_width_px > 0 else 0
        
        return True, score, scale_factor, ref_width_px, ref_width_cm
    
    def get_scale_factor(self):
        return self.scale_factor
    
    def get_detected_object(self):
        return self.detected_object
    
    def reset(self):
        self.detected_object = None
        self.scale_factor = None