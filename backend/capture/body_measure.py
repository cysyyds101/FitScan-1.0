"""
body_measure.py — 人体测量算法（轻量几何方法）。

不使用任何 ML / 深度学习模型，纯几何 + 统计方法。

算法概览：
1. 背景估计：从深度直方图中找出主峰（背景平面）
2. 前景提取：分离出深度明显近于背景的人体区域
3. 人体包围盒：确定像素级边界（top / bottom / left / right）
4. 像素→毫米换算：用相机内参 + 深度值把像素尺寸转为实际毫米
5. 身高：包围盒底部到顶部
6. 肩宽：躯干上部最宽处（30-40% 高度区间）
7. 臂长：躯干侧面到手臂末端的像素宽度 × 深度换算

相机内参（Intel RealSense SR300 / D400 通用近似值）：
    fx ≈ fy ≈ 480   (像素焦距)
    cx = 320         (主点 X)
    cy = 240         (主点 Y)
    hfov ≈ 73°       (标称值)
    vfov ≈ 59°       (标定值)
"""
from __future__ import annotations

import json
import math
import struct
from dataclasses import dataclass, asdict
from typing import NamedTuple


# ─── 相机内参（Intel RealSense SR300 / D400）────────────────────────────────────

class CameraIntrinsics(NamedTuple):
    fx: float      # 焦距 X（像素）
    fy: float      # 焦距 Y（像素）
    cx: float      # 主点 X
    cy: float      # 主点 Y
    hfov_deg: float  # 水平视场角（度）
    vfov_deg: float  # 垂直视场角（度）

    def px_to_mm_h(self, depth_mm: float) -> float:
        """像素宽度 → 毫米（水平方向）。"""
        return depth_mm * math.tan(math.radians(self.hfov_deg) / 2) * 2 / self.fx

    def px_to_mm_v(self, depth_mm: float) -> float:
        """像素高度 → 毫米（垂直方向）。"""
        return depth_mm * math.tan(math.radians(self.vfov_deg) / 2) * 2 / self.fy


# RealSense SR300 / D415 / D455 通用近似
REALSENSE_INTRINSICS = CameraIntrinsics(
    fx=480.0,
    fy=480.0,
    cx=320.0,
    cy=240.0,
    hfov_deg=73.0,
    vfov_deg=59.0,
)


# ─── 测量结果数据结构 ───────────────────────────────────────────────────────────

@dataclass
class BodyMeasurements:
    """输出 JSON 结构（所有长度单位：厘米 cm）。"""
    height_cm:        float | None  # 身高
    shoulder_width_cm: float | None  # 肩宽
    arm_length_cm:    float | None  # 臂长（估算）
    confidence:       float         # 置信度 0-1（前景像素占比）
    avg_depth_cm:     float         # 平均前景深度（cm）

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, d: dict) -> BodyMeasurements:
        return cls(**d)


# ─── 深度图像处理工具 ───────────────────────────────────────────────────────────

# 深度值范围（毫米）
NEAR_MM = 400    # 小于此值忽略（镜头近处噪声）
FAR_MM  = 2500   # 大于此值忽略（远处背景）
HISTOGRAM_BINS = 256


def compute_depth_histogram(depth: list[float], bins: int = HISTOGRAM_BINS) -> list[int]:
    """计算深度直方图（用于背景峰值检测）。"""
    hist = [0] * bins
    mn, mx = FAR_MM, NEAR_MM
    for d in depth:
        if NEAR_MM <= d <= FAR_MM:
            if d < mn: mn = d
            if d > mx: mx = d
    if mx <= mn:
        return hist
    rng = mx - mn
    for d in depth:
        if NEAR_MM <= d <= FAR_MM:
            b = int((d - mn) / rng * (bins - 1))
            hist[min(b, bins - 1)] += 1
    return hist


def find_bg_depth_peak(depth: list[float]) -> float:
    """从深度直方图找主峰 → 估计背景深度（毫米）。"""
    hist = compute_depth_histogram(depth)
    peak_bin = max(range(len(hist)), key=lambda i: hist[i])
    mn, mx = FAR_MM, NEAR_MM
    for d in depth:
        if NEAR_MM <= d <= FAR_MM:
            if d < mn: mn = d
            if d > mx: mx = d
    rng = mx - mn if mx > mn else 1
    return mn + peak_bin / (len(hist) - 1) * rng


# ─── 前景提取 ──────────────────────────────────────────────────────────────────

@dataclass
class PersonBounds:
    """人体像素包围盒。"""
    top: int; bottom: int   # 行索引
    left: int; right: int   # 列索引
    pixel_count: int        # 前景像素总数


def extract_foreground(
    depth: list[float],
    width: int,
    height: int,
    bg_depth_mm: float,
    fg_threshold_mm: float = 150.0,  # 与背景差值阈值
    min_pixels: int = 2000,          # 最小前景像素
) -> tuple[list[tuple[int, int]], PersonBounds | None]:
    """
    从深度图提取前景人体区域。

    Args:
        depth:        扁平化 float32 深度数组（毫米）
        width/height: 图像尺寸
        bg_depth_mm:  背景深度估计（毫米）
        fg_threshold: 前景判定阈值：|pixel_depth - bg_depth| > threshold
        min_pixels:   小于此像素数认为无人

    Returns:
        (前景像素坐标列表, PersonBounds | None)
    """
    min_row, max_row = height, 0
    min_col, max_col = width, 0
    fg_pixels: list[tuple[int, int]] = []

    for idx, d in enumerate(depth):
        if d < NEAR_MM or d > FAR_MM:
            continue
        if abs(d - bg_depth_mm) > fg_threshold_mm:
            row = idx // width
            col = idx % width
            fg_pixels.append((row, col))
            if row < min_row: min_row = row
            if row > max_row: max_row = row
            if col < min_col: min_col = col
            if col > max_col: max_col = col

    if len(fg_pixels) < min_pixels:
        return [], None

    return fg_pixels, PersonBounds(
        top=min_row, bottom=max_row,
        left=min_col, right=max_col,
        pixel_count=len(fg_pixels),
    )


# ─── 核心测量算法 ─────────────────────────────────────────────────────────────

def find_edge_at_row(
    fg_mask: list[list[bool]],
    row: int,
    direction: str,   # 'left' | 'right'
    x_start: int,
    x_end: int,
) -> int:
    """在指定行从指定方向扫描，找到前景边缘的 X 坐标。"""
    h = len(fg_mask)
    w = len(fg_mask[0]) if h > 0 else 0
    if direction == 'left':
        for x in range(x_start, x_end):
            if 0 <= row < h and 0 <= x < w and fg_mask[row][x]:
                return x
        return x_start
    else:
        for x in range(x_start, x_end, -1):
            if 0 <= row < h and 0 <= x < w and fg_mask[row][x]:
                return x
        return x_start


def scan_row_widths(
    fg_mask: list[list[bool]],
    row: int,
    x_min: int,
    x_max: int,
) -> tuple[int, int] | None:
    """扫描一行，返回 (left_edge, right_edge)。无前景返回 None。"""
    left = right = None
    for x in range(x_min, x_max):
        if fg_mask[row][x]:
            if left is None: left = x
            right = x
    if left is None:
        return None
    return left, right


def compute_measurements(
    depth: list[float],
    width: int,
    height: int,
    intrinsics: CameraIntrinsics = REALSENSE_INTRINSICS,
) -> BodyMeasurements:
    """
    给定一帧深度图像，计算人体基础测量值。

    Args:
        depth:       扁平化 float32 深度数组（毫米），长度为 width * height
        width/height: 图像尺寸

    Returns:
        BodyMeasurements（含 height_cm / shoulder_width_cm / arm_length_cm）
    """
    # Step 1: 背景估计
    bg_depth_mm = find_bg_depth_peak(depth)
    bg_depth_cm = bg_depth_mm / 10.0

    # Step 2: 前景提取
    fg_pixels, bounds = extract_foreground(depth, width, height, bg_depth_mm)
    if bounds is None or bounds.pixel_count < 2000:
        return BodyMeasurements(
            height_cm=None, shoulder_width_cm=None, arm_length_cm=None,
            confidence=0.0, avg_depth_cm=bg_depth_cm,
        )

    # Step 3: 建立前景 mask（用于快速查找）
    fg_mask: list[list[bool]] = [[False] * width for _ in range(height)]
    for row, col in fg_pixels:
        fg_mask[row][col] = True

    # Step 4: 计算平均深度
    avg_depth_mm = sum(d for d in depth if NEAR_MM <= d <= FAR_MM) / len([
        d for d in depth if NEAR_MM <= d <= FAR_MM
    ])
    avg_depth_cm = avg_depth_mm / 10.0

    # Step 5: 像素 → 毫米换算
    px_per_mm_h = intrinsics.px_to_mm_h(avg_depth_mm)
    px_per_mm_v = intrinsics.px_to_mm_v(avg_depth_mm)
    mm_per_px_h = 1.0 / px_per_mm_h if px_per_mm_h > 0 else 1.0
    mm_per_px_v = 1.0 / px_per_mm_v if px_per_mm_v > 0 else 1.0

    person_height_px = bounds.bottom - bounds.top
    person_width_px  = bounds.right - bounds.left

    # Step 6: 身高
    if person_height_px > 0:
        height_mm = person_height_px * px_per_mm_v
        # 根据人体比例修正（头部+躯干+腿 ≈ 85% 像素高度）
        height_mm /= 0.85
        height_cm = round(height_mm / 10, 1)
    else:
        height_cm = None

    # Step 7: 肩宽
    # 在躯干上部区域（top + 25-40% 身高）扫描最宽处
    shoulder_top = bounds.top + int(person_height_px * 0.25)
    shoulder_bot = bounds.top + int(person_height_px * 0.40)
    max_shoulder_width_px = 0

    for row in range(shoulder_top, min(shoulder_bot, height)):
        edges = scan_row_widths(fg_mask, row, bounds.left, bounds.right)
        if edges:
            w = edges[1] - edges[0]
            if w > max_shoulder_width_px:
                max_shoulder_width_px = w

    if max_shoulder_width_px > 0:
        shoulder_width_mm = max_shoulder_width_px * px_per_mm_h
        # 加 5% 修正（实际肩膀略宽于前景像素）
        shoulder_width_cm = round(shoulder_width_mm / 10 * 1.05, 1)
    else:
        shoulder_width_cm = None

    # Step 8: 臂长（基于躯干侧面宽度估算）
    # 在手臂区域（top + 40-65% 身高）估算
    arm_top = bounds.top + int(person_height_px * 0.40)
    arm_bot = bounds.top + int(person_height_px * 0.65)
    torso_width_at_arm = 0
    arm_width_max = 0

    for row in range(arm_top, min(arm_bot, height)):
        edges = scan_row_widths(fg_mask, row, bounds.left, bounds.right)
        if edges:
            row_w = edges[1] - edges[0]
            # 躯干宽度取中间行
            if shoulder_top <= row <= shoulder_bot:
                if row_w > torso_width_at_arm:
                    torso_width_at_arm = row_w
            if row_w > arm_width_max:
                arm_width_max = row_w

    if arm_width_max > 0 and torso_width_at_arm > 0:
        # 手臂 ≈ 总宽度 - 躯干宽度（两侧各一半）
        arm_px_single = max(0, (arm_width_max - torso_width_at_arm) // 2)
        # 按人体比例（臂长 ≈ 身高 × 0.4）换算
        if height_cm:
            arm_length_cm = round(height_cm * 0.4, 1)
        else:
            arm_length_mm = arm_px_single * px_per_mm_h * 1.5  # 修正系数
            arm_length_cm = round(arm_length_mm / 10, 1)
    else:
        # 回退：按身高比例估算
        arm_length_cm = round(height_cm * 0.4, 1) if height_cm else None

    # Step 9: 置信度（前景像素占包围盒比例）
    box_pixels = (bounds.bottom - bounds.top) * (bounds.right - bounds.left)
    confidence = round(bounds.pixel_count / box_pixels, 3) if box_pixels > 0 else 0.0

    return BodyMeasurements(
        height_cm=height_cm,
        shoulder_width_cm=shoulder_width_cm,
        arm_length_cm=arm_length_cm,
        confidence=confidence,
        avg_depth_cm=avg_depth_cm,
    )


# ─── 便捷入口 ─────────────────────────────────────────────────────────────────

def measure_depth_frame(frame_bytes: bytes, width: int, height: int) -> BodyMeasurements:
    """
    给定二进制深度帧（640×480×4 bytes float32），返回测量结果。
    用于 capture.py 直接调用。
    """
    depth = list(struct.unpack(f'<{width * height}f', frame_bytes))
    return compute_measurements(depth, width, height)


def measure_from_raw(data: bytes, width: int, height: int) -> tuple[BodyMeasurements, bytes]:
    """
    给定包含 header + \\n + binary 的完整消息，返回 (测量结果, 纯二进制部分)。

    协议格式：
        JSON header bytes + b'\\n' + binary depth frame
    """
    nl = data.index(b'\n')
    header = json.loads(data[:nl].decode())
    frame_bytes = data[nl + 1:]
    measurements = measure_depth_frame(frame_bytes, width, height)
    return measurements, frame_bytes
