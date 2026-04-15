import cv2
import math
import numpy as np
import time

from src.config.config import Config


class Visualizer:
    def __init__(self):
        self.default_sidebar_width = getattr(Config, "SIDEBAR_WIDTH", 380)
        self.min_sidebar_width = 280  # 最小侧边栏宽度
        self.max_sidebar_width = 450  # 最大侧边栏宽度
        self.theme = getattr(Config, "VISUAL_THEME", {})
        self.stage_labels = getattr(Config, "STAGE_LABELS", {})
        self.display_measurements = getattr(Config, "DISPLAY_MEASUREMENTS", [])
        self.radar_dimensions = getattr(Config, "RADAR_DIMENSIONS", [])
        self.radar_center_x = getattr(Config, "RADAR_CENTER_X", 190)
        self.radar_center_y = getattr(Config, "RADAR_CENTER_Y", 120)
        self.radar_radius = getattr(Config, "RADAR_RADIUS", 65)
        
        # 动画状态
        self.animation_time = time.time()
        self.pulse_value = 1.0
        self.fade_value = 1.0
        
        # 图标映射
        self.icons = {
            "height": "📏",
            "shoulder": "👤",
            "chest": "👕",
            "waist": "🩳",
            "hip": "👖",
            "calibration": "🎯",
            "measurement": "📊",
            "recommendation": "👗",
            "success": "✅",
            "warning": "⚠️",
            "info": "ℹ️"
        }

    def _color(self, key, default_value):
        return self.theme.get(key, default_value)

    def _format_value(self, value, suffix=" cm"):
        if value is None:
            return "--"
        try:
            return f"{float(value):.1f}{suffix}"
        except (TypeError, ValueError):
            return str(value)

    def _update_animations(self):
        """更新动画状态"""
        current_time = time.time()
        delta_time = current_time - self.animation_time
        self.animation_time = current_time
        
        # 脉冲动画
        self.pulse_value = 1.0 + 0.1 * math.sin(current_time * 2)
        
        # 淡入动画
        if self.fade_value < 1.0:
            self.fade_value = min(1.0, self.fade_value + delta_time * 2)

    def _draw_pulse_effect(self, image, center, radius, color, max_radius=100):
        """绘制脉冲效果"""
        pulse_radius = radius * self.pulse_value
        alpha = 0.5 * (1 - abs(self.pulse_value - 1.0) / 0.1)
        
        # 绘制脉冲环
        for i in range(3):
            current_radius = radius + (max_radius - radius) * (i + 1) / 3
            current_alpha = alpha * (1 - i / 3)
            
            if current_alpha > 0:
                pulse_color = (
                    int(color[0] * current_alpha),
                    int(color[1] * current_alpha),
                    int(color[2] * current_alpha)
                )
                cv2.circle(image, center, int(current_radius), pulse_color, 2, cv2.LINE_AA)

    def _draw_fade_effect(self, image, region, color, alpha):
        """绘制淡入淡出效果"""
        x1, y1, x2, y2 = region
        overlay = image.copy()
        cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
        cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0, image)

    def _draw_icon(self, image, icon_name, position, scale=1.0, color=None):
        """绘制图标"""
        icon = self.icons.get(icon_name, "ℹ️")
        color = color or self._color("text", (250, 250, 255))
        
        # 绘制图标（使用文本模拟）
        cv2.putText(
            image,
            icon,
            position,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6 * scale,
            color,
            1,
            cv2.LINE_AA
        )

    def _draw_button(self, image, text, position, size, is_hover=False, is_clicked=False):
        """绘制带有交互效果的按钮"""
        x, y = position
        width, height = size
        
        # 按钮背景
        if is_clicked:
            bg_color = self._color("accent", (64, 158, 255))
        elif is_hover:
            bg_color = self._color("hover_bg", (48, 56, 72))
        else:
            bg_color = self._color("panel_alt", (40, 48, 64))
        
        # 绘制按钮
        self._draw_rounded_rectangle(
            image,
            (x, y),
            (x + width, y + height),
            bg_color,
            radius=8
        )
        
        # 按钮边框
        border_color = self._color("accent", (64, 158, 255)) if is_hover or is_clicked else self._color("border", (64, 72, 88))
        self._draw_rounded_rectangle(
            image,
            (x, y),
            (x + width, y + height),
            border_color,
            radius=8,
            thickness=2
        )
        
        # 按钮文本
        text_size, _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
        text_x = x + (width - text_size[0]) // 2
        text_y = y + (height + text_size[1]) // 2
        cv2.putText(
            image,
            text,
            (text_x, text_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            self._color("text", (250, 250, 255)),
            2,
            cv2.LINE_AA
        )
        
        return (x, y, x + width, y + height)

    def _normalize_stage_text(self, stage_text=None, stage_key=None):
        if stage_text:
            return stage_text
        if stage_key and stage_key in self.stage_labels:
            return self.stage_labels[stage_key]
        return self.stage_labels.get("scanning", "Step 2 扫描中")

    def _normalize_reference_name(self, reference_object):
        if isinstance(reference_object, dict):
            return (
                reference_object.get("label")
                or reference_object.get("name")
                or reference_object.get("type")
                or "未识别"
            )
        if isinstance(reference_object, str) and reference_object:
            config_obj = getattr(Config, "REFERENCE_OBJECTS", {}).get(reference_object)
            if isinstance(config_obj, dict):
                return config_obj.get("label", reference_object)
            return reference_object
        return "未识别"

    def _normalize_recommendation(self, recommended_size):
        if isinstance(recommended_size, dict):
            primary = recommended_size.get("primary") or recommended_size.get("regular_fit") or "--"
            return {
                "primary": primary,
                "regular_fit": recommended_size.get("regular_fit", primary),
                "slim_fit": recommended_size.get("slim_fit", primary),
                "loose_fit": recommended_size.get("loose_fit", primary),
            }

        if isinstance(recommended_size, str):
            return {
                "primary": recommended_size,
                "regular_fit": recommended_size,
                "slim_fit": recommended_size,
                "loose_fit": recommended_size,
            }

        return {
            "primary": "--",
            "regular_fit": "--",
            "slim_fit": "--",
            "loose_fit": "--",
        }

    def _draw_text(self, image, text, position, scale=0.55, color=None, thickness=1):
        cv2.putText(
            image,
            text,
            position,
            cv2.FONT_HERSHEY_SIMPLEX,
            scale,
            color or self._color("text", (255, 255, 255)),
            thickness,
            cv2.LINE_AA,
        )

    def _draw_rounded_rectangle(self, image, top_left, bottom_right, color, radius=8, thickness=-1):
        """绘制圆角矩形"""
        x1, y1 = top_left
        x2, y2 = bottom_right
        
        # 绘制矩形的4个角
        cv2.ellipse(image, (x1 + radius, y1 + radius), (radius, radius), 180, 0, 90, color, thickness)
        cv2.ellipse(image, (x2 - radius, y1 + radius), (radius, radius), 270, 0, 90, color, thickness)
        cv2.ellipse(image, (x1 + radius, y2 - radius), (radius, radius), 90, 0, 90, color, thickness)
        cv2.ellipse(image, (x2 - radius, y2 - radius), (radius, radius), 0, 0, 90, color, thickness)
        
        # 绘制矩形的4条边
        cv2.rectangle(image, (x1 + radius, y1), (x2 - radius, y2), color, thickness)
        cv2.rectangle(image, (x1, y1 + radius), (x2, y2 - radius), color, thickness)

    def _draw_section_title(self, sidebar, title, y):
        # 绘制圆角背景
        self._draw_rounded_rectangle(
            sidebar,
            (16, y - 18),
            (self.sidebar_width - 16, y + 14),
            self._color("panel_alt", (43, 51, 66)),
            radius=6
        )
        # 添加阴影效果
        cv2.rectangle(
            sidebar,
            (18, y - 16),
            (self.sidebar_width - 14, y + 16),
            self._color("shadow", (0, 0, 0)),
            1
        )
        # 绘制标题文本
        self._draw_text(sidebar, title, (28, y + 4), scale=0.58, color=self._color("accent", (83, 172, 255)), thickness=2)
        return y + 36

    def _draw_info_row(self, sidebar, label, value, y):
        # 绘制标签
        self._draw_text(sidebar, label, (24, y), scale=0.5, color=self._color("muted_text", (185, 192, 203)), thickness=1)
        
        # 绘制值的背景
        value_str = str(value)
        (text_width, text_height), _ = cv2.getTextSize(value_str, cv2.FONT_HERSHEY_SIMPLEX, 0.54, 2)
        self._draw_rounded_rectangle(
            sidebar,
            (140, y - text_height - 4),
            (self.sidebar_width - 24, y + 4),
            self._color("hover_bg", (48, 56, 72)),
            radius=4
        )
        # 绘制值文本
        self._draw_text(sidebar, value_str, (145, y), scale=0.54, color=self._color("text", (245, 247, 250)), thickness=2)
        return y + 30

    def draw_measurement_line(self, frame, start_point, end_point, label, color=None):
        color = color or self._color("line", (96, 165, 250))
        x1, y1 = int(start_point[0]), int(start_point[1])
        x2, y2 = int(end_point[0]), int(end_point[1])

        # 绘制主线（更粗的线条）
        cv2.line(frame, (x1, y1), (x2, y2), color, 3, cv2.LINE_AA)
        
        # 绘制光晕效果
        cv2.line(frame, (x1, y1), (x2, y2), (255, 255, 255), 1, cv2.LINE_AA)
        
        # 绘制端点（带光晕的圆形）
        cv2.circle(frame, (x1, y1), 6, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.circle(frame, (x1, y1), 4, color, -1, cv2.LINE_AA)
        cv2.circle(frame, (x2, y2), 6, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.circle(frame, (x2, y2), 4, color, -1, cv2.LINE_AA)

        mid_x = int((x1 + x2) / 2)
        mid_y = int((y1 + y2) / 2)

        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.55
        thickness = 2
        text_size, baseline = cv2.getTextSize(label, font, scale, thickness)
        padding_x = 10
        padding_y = 8

        # 计算标签位置，确保在画面内
        box_x1 = max(mid_x - text_size[0] // 2 - padding_x, 0)
        box_y1 = max(mid_y - text_size[1] - padding_y - 10, 0)
        box_x2 = min(box_x1 + text_size[0] + padding_x * 2, frame.shape[1] - 1)
        box_y2 = min(box_y1 + text_size[1] + padding_y * 2 + baseline, frame.shape[0] - 1)

        # 绘制标签背景（圆角矩形）
        self._draw_rounded_rectangle(
            frame, 
            (box_x1, box_y1), 
            (box_x2, box_y2), 
            self._color("line_label_bg", (12, 16, 24)),
            radius=6
        )
        
        # 绘制标签边框
        self._draw_rounded_rectangle(
            frame, 
            (box_x1, box_y1), 
            (box_x2, box_y2), 
            color,
            radius=6, 
            thickness=1
        )
        
        # 绘制标签文本
        text_x = box_x1 + padding_x
        text_y = box_y2 - padding_y - baseline + 2
        cv2.putText(
            frame,
            label,
            (text_x, text_y),
            font,
            scale,
            self._color("line_label_text", (255, 255, 255)),
            thickness,
            cv2.LINE_AA,
        )

        return frame

    def draw_radar_chart(self, sidebar, measurements, y_position):
        """
        绘制雷达图（体型分析）
        
        参数:
            sidebar: 侧边栏图像
            measurements: 测量数据字典
            y_position: 雷达图起始 Y 位置
        """
        if not self.radar_dimensions:
            return y_position
        
        # 雷达图区域背景
        chart_height = 220
        self._draw_rounded_rectangle(
            sidebar,
            (16, y_position - 10),
            (self.sidebar_width - 16, y_position + chart_height),
            self._color("panel_alt", (40, 48, 64)),
            radius=12
        )
        
        # 标题
        self._draw_text(sidebar, "体型分析", (28, y_position + 10), scale=0.58, color=self._color("accent", (64, 158, 255)), thickness=2)
        
        # 雷达图参数
        center_x = self.sidebar_width // 2
        center_y = y_position + 70
        radius = 65
        num_axes = len(self.radar_dimensions)
        angle_step = 2 * math.pi / num_axes
        
        # 绘制雷达图背景（多边形网格）
        levels = 5
        for level in range(1, levels + 1):
            level_radius = radius * level / levels
            points = []
            for i in range(num_axes):
                angle = i * angle_step - math.pi / 2  # 从顶部开始
                x = center_x + level_radius * math.cos(angle)
                y = center_y + level_radius * math.sin(angle)
                points.append([int(x), int(y)])
            # 绘制网格线
            cv2.polylines(sidebar, [np.array(points)], True, self._color("border", (64, 72, 88)), 1, cv2.LINE_AA)
        
        # 绘制轴线
        for i in range(num_axes):
            angle = i * angle_step - math.pi / 2
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            # 绘制轴线
            cv2.line(sidebar, (center_x, center_y), (int(x), int(y)), self._color("border", (64, 72, 88)), 1, cv2.LINE_AA)
            
            # 轴标签
            dim_key, dim_label, max_val, min_val = self.radar_dimensions[i]
            label_x = center_x + (radius + 18) * math.cos(angle)
            label_y = center_y + (radius + 18) * math.sin(angle)
            # 标签背景
            (text_width, text_height), _ = cv2.getTextSize(dim_label, cv2.FONT_HERSHEY_SIMPLEX, 0.35, 1)
            self._draw_rounded_rectangle(
                sidebar,
                (int(label_x) - text_width//2 - 6, int(label_y) - text_height//2 - 4),
                (int(label_x) + text_width//2 + 6, int(label_y) + text_height//2 + 4),
                self._color("hover_bg", (48, 56, 72)),
                radius=4
            )
            # 标签文本
            self._draw_text(sidebar, dim_label, (int(label_x) - text_width//2, int(label_y) + text_height//2), scale=0.35, color=self._color("radar_label", (240, 240, 245)), thickness=1)
        
        # 绘制数据多边形
        measurements = measurements or {}
        data_points = []
        for i, (dim_key, dim_label, max_val, min_val) in enumerate(self.radar_dimensions):
            value = measurements.get(dim_key, 0)
            if value is None:
                value = 0
            
            # 归一化到 0-1 范围
            normalized = (value - min_val) / (max_val - min_val) if max_val != min_val else 0.5
            normalized = max(0, min(1, normalized))  # 限制在 0-1 之间
            
            angle = i * angle_step - math.pi / 2
            x = center_x + radius * normalized * math.cos(angle)
            y = center_y + radius * normalized * math.sin(angle)
            data_points.append([int(x), int(y)])
        
        if data_points:
            # 创建渐变填充
            for i in range(1, 10):
                alpha = i / 10
                scaled_points = []
                for point in data_points:
                    dx = point[0] - center_x
                    dy = point[1] - center_y
                    scaled_points.append([
                        int(center_x + dx * alpha),
                        int(center_y + dy * alpha)
                    ])
                # 绘制渐变层
                cv2.fillPoly(
                    sidebar, 
                    [np.array(scaled_points)], 
                    (
                        int(self._color("radar_line", (64, 158, 255))[0] * alpha + 40 * (1 - alpha)),
                        int(self._color("radar_line", (64, 158, 255))[1] * alpha + 48 * (1 - alpha)),
                        int(self._color("radar_line", (64, 158, 255))[2] * alpha + 64 * (1 - alpha))
                    )
                )
            # 绘制多边形边框
            cv2.polylines(sidebar, [np.array(data_points)], True, self._color("radar_line", (64, 158, 255)), 2, cv2.LINE_AA)
            # 绘制数据点
            for point in data_points:
                cv2.circle(sidebar, point, 5, (255, 255, 255), 1, cv2.LINE_AA)
                cv2.circle(sidebar, point, 3, self._color("radar_line", (64, 158, 255)), -1, cv2.LINE_AA)
        
        return y_position + chart_height + 10

    def draw_sidebar(
        self,
        frame,
        measurements,
        recommended_size,
        scale_factor,
        stage_text=None,
        stage_key=None,
        reference_object=None,
    ):
        if frame is None:
            return frame

        # 更新动画状态
        self._update_animations()

        height, width = frame.shape[:2]
        
        # 动态计算侧边栏宽度，确保摄像头显示区域有足够空间
        # 侧边栏宽度不应超过窗口宽度的1/3
        max_sidebar_width = min(self.max_sidebar_width, width // 3)
        # 侧边栏宽度不应小于最小值
        self.sidebar_width = max(self.min_sidebar_width, min(max_sidebar_width, self.default_sidebar_width))
        
        sidebar = frame.copy()

        # 绘制侧边栏背景（渐变效果）
        for i in range(self.sidebar_width):
            alpha = i / self.sidebar_width
            color = (
                int(self._color("bg", (20, 24, 32))[0] * (1 - alpha) + 10 * alpha),
                int(self._color("bg", (20, 24, 32))[1] * (1 - alpha) + 14 * alpha),
                int(self._color("bg", (20, 24, 32))[2] * (1 - alpha) + 20 * alpha)
            )
            cv2.line(sidebar, (width - self.sidebar_width + i, 0), (width - self.sidebar_width + i, height), color, 1)

        # 绘制侧边栏边框
        cv2.rectangle(
            sidebar,
            (width - self.sidebar_width, 0),
            (width - self.sidebar_width + 3, height),
            self._color("accent", (64, 158, 255)),
            -1,
        )

        # 绘制主面板
        panel = sidebar[:, width - self.sidebar_width:width]
        
        # 绘制圆角面板
        self._draw_rounded_rectangle(
            panel, 
            (10, 14), 
            (self.sidebar_width - 10, height - 14), 
            self._color("panel", (30, 36, 48)),
            radius=12
        )
        
        # 绘制面板边框
        self._draw_rounded_rectangle(
            panel, 
            (10, 14), 
            (self.sidebar_width - 10, height - 14), 
            self._color("border", (64, 72, 88)),
            radius=12, 
            thickness=1
        )

        # 绘制标题区域
        y = 40
        # 标题背景
        self._draw_rounded_rectangle(
            panel, 
            (20, 25), 
            (self.sidebar_width - 20, 55), 
            self._color("panel_alt", (40, 48, 64)),
            radius=8
        )
        # 标题图标
        self._draw_icon(panel, "measurement", (25, 38))
        # 标题文本
        self._draw_text(panel, "FitScan 智能测量", (55, y), scale=0.8, color=self._color("text", (250, 250, 255)), thickness=2)
        
        # 副标题
        self._draw_text(panel, "智能人体尺寸估算系统", (55, y + 20), scale=0.45, color=self._color("muted_text", (170, 180, 190)), thickness=1)
        y += 45
        
        # 阶段标签
        stage_label = self._normalize_stage_text(stage_text=stage_text, stage_key=stage_key)
        stage_color = self._color("success", (52, 211, 153))
        self._draw_rounded_rectangle(
            panel, 
            (24, y - 18), 
            (self.sidebar_width - 24, y + 10), 
            stage_color,
            radius=6
        )
        # 阶段图标
        self._draw_icon(panel, "calibration", (30, y - 12), color=self._color("bg", (20, 24, 32)))
        # 阶段文本
        self._draw_text(panel, stage_label, (60, y + 2), scale=0.58, color=self._color("bg", (20, 24, 32)), thickness=2)
        # 脉冲效果
        self._draw_pulse_effect(panel, (35, y - 7), 10, stage_color, max_radius=30)
        y += 34

        # 识别状态
        y = self._draw_section_title(panel, "识别状态", y)
        self._draw_icon(panel, "info", (20, y - 20))
        y = self._draw_info_row(panel, "参照物", self._normalize_reference_name(reference_object), y)
        y = self._draw_info_row(panel, "比例系数 K", self._format_value(scale_factor, " cm/px"), y)

        # 核心尺寸
        y = self._draw_section_title(panel, "核心尺寸", y)
        measurements = measurements or {}
        for key, label in self.display_measurements:
            # 绘制尺寸图标
            icon_name = key if key in self.icons else "info"
            self._draw_icon(panel, icon_name, (20, y - 20))
            y = self._draw_info_row(panel, label, self._format_value(measurements.get(key)), y)

        # 绘制雷达图（体型分析）
        y = self.draw_radar_chart(panel, measurements, y)

        # 尺码推荐
        recommendation = self._normalize_recommendation(recommended_size)
        y = self._draw_section_title(panel, "尺码推荐", y)
        self._draw_icon(panel, "recommendation", (20, y - 20))
        
        # 格式化输出：L（宽松版）/ S（修身版）
        size_format = f"{recommendation.get('loose_fit', '--')}（宽松版）/ {recommendation.get('slim_fit', '--')}（修身版）"
        y = self._draw_info_row(panel, "推荐尺码", size_format, y)
        
        y = self._draw_info_row(panel, "修身版", recommendation.get("slim_fit", "--"), y)
        y = self._draw_info_row(panel, "常规版", recommendation.get("regular_fit", "--"), y)
        y = self._draw_info_row(panel, "宽松版", recommendation.get("loose_fit", "--"), y)

        # 添加操作按钮
        if y + 80 < height - 40:
            # 重新校准按钮
            self._draw_button(panel, "重新校准", (40, y), (120, 36))
            # 保存结果按钮
            self._draw_button(panel, "保存结果", (180, y), (120, 36))
            y += 45

        # 页脚信息
        footer_y = height - 36
        self._draw_text(
            panel,
            "核心维度仅供演示参考",
            (24, footer_y),
            scale=0.48,
            color=self._color("muted_text", (170, 180, 190)),
            thickness=1,
        )
        
        # 版本信息
        self._draw_text(
            panel,
            "v1.0.0",
            (self.sidebar_width - 60, footer_y),
            scale=0.45,
            color=self._color("muted_text", (170, 180, 190)),
            thickness=1,
        )

        output = frame.copy()
        output[:, width - self.sidebar_width:width] = sidebar[:, width - self.sidebar_width:width]
        return output