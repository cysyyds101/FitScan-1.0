class Config:
    # ========== 摄像头设置 ==========
    CAMERA_ID = 0
    CAMERA_WIDTH = 1280
    CAMERA_HEIGHT = 720
    CAMERA_FPS = 30

    # ========== MediaPipe 设置 ==========
    POSE_MIN_DETECTION_CONFIDENCE = 0.7
    POSE_MIN_TRACKING_CONFIDENCE = 0.7
    POSE_MODEL_COMPLEXITY = 1
    POSE_LANDMARKS = 33

    # ========== 参照物配置 ==========
    REFERENCE_OBJECTS = {
        "A4": {
            "width": 21.0,
            "height": 29.7,
            "label": "A4 纸",
            "min_area": 1000,
            "max_area": 50000,
            "min_pixel": 100,
            "max_pixel": 320,
            "aspect_ratio": 29.7 / 21.0,  # 长宽比
        },
        "ID_CARD": {
            "width": 8.56,
            "height": 5.398,
            "label": "身份证",
            "min_area": 500,
            "max_area": 12000,
            "min_pixel": 50,
            "max_pixel": 180,
            "aspect_ratio": 8.56 / 5.398,
        },
        "BANK_CARD": {
            "width": 8.56,
            "height": 5.398,
            "label": "银行卡",
            "min_area": 500,
            "max_area": 12000,
            "min_pixel": 50,
            "max_pixel": 180,
            "aspect_ratio": 8.56 / 5.398,
        },
    }

    # ========== 参照物检测参数 ==========
    CANNY_THRESHOLD1 = 30
    CANNY_THRESHOLD2 = 100
    GAUSSIAN_KERNEL_SIZE = 5
    CONTOUR_APPROX_EPSILON = 0.02  # 降低近似容差，提高检测精度
    REFERENCE_MIN_PERIMETER = 50
    REFERENCE_MATCH_MIN_SCORE = 3.0
    REFERENCE_ASPECT_TOLERANCE = 0.5  # 放宽长宽比容差
    REFERENCE_RECTANGULARITY_MIN = 0.5

    # ========== 几何与经验估算参数 ==========
    # 身高校正
    HEIGHT_CORRECTION_FACTOR = 1.05  # 从鼻尖到头顶的校正因子
    HEIGHT_TOP_OFFSET_FACTOR = 1.0  # 身高顶部偏移因子（已修复，不再额外放大）

    # 围度估算系数（经验公式法）
    CHEST_CIRCUMFERENCE_FACTOR = 1.8  # 胸宽 -> 胸围
    CHEST_WIDTH_RATIO = 1.1  # 胸宽 / 肩宽
    WAIST_WIDTH_RATIO = 0.65  # 腰宽 / 肩宽
    WAIST_WIDTH_FROM_SHOULDER_RATIO = 0.75  # 腰宽估算系数
    NECK_WIDTH_RATIO = 0.25  # 颈宽 / 肩宽
    NECK_CIRCUMFERENCE_FACTOR = 3.14159 * 1.1  # 颈围系数
    WAIST_CIRCUMFERENCE_FACTOR = 3.14159 * 1.1  # 腰围系数
    HIP_CIRCUMFERENCE_FACTOR = 3.14159 * 1.2  # 臀围系数
    CHEST_CIRCUMFERENCE_ELLIPSE_FACTOR = 3.14159 * 1.1  # 椭圆拟合法胸围系数
    DEPTH_SCALE_FACTOR = 0.1  # Z 轴深度缩放因子

    # ========== 滤波与稳定性 ==========
    FILTER_WINDOW_SIZE = 5
    ENABLE_SMOOTHING = True
    SMOOTHING_FACTOR = 0.3
    ENABLE_MULTI_FRAME_AVERAGE = True
    MULTI_FRAME_COUNT = 5

    # ========== 尺寸测量增强参数 ==========
    ENABLE_DETAILED_MEASUREMENTS = True
    MEASUREMENT_PRECISION = 1  # 精度：1 位小数

    # ========== 可视化设置 ==========
    SIDEBAR_WIDTH = 380  # 加宽侧边栏以容纳雷达图和更多信息
    FONT_SCALE = 0.7
    LINE_THICKNESS = 2
    RADAR_CHART_SIZE = 180  # 雷达图尺寸
    RADAR_CENTER_X = 190  # 雷达图中心 X（相对于侧边栏）
    RADAR_CENTER_Y = 120  # 雷达图中心 Y（相对于侧边栏）
    RADAR_RADIUS = 65  # 雷达图半径

    VISUAL_THEME = {
        "bg": (20, 24, 32),  # 更深的背景色
        "panel": (30, 36, 48),  # 面板背景
        "panel_alt": (40, 48, 64),  # 交替面板背景
        "text": (250, 250, 255),  # 主文本色
        "muted_text": (170, 180, 190),  # 次要文本色
        "accent": (64, 158, 255),  # 主强调色（科技蓝）
        "success": (52, 211, 153),  # 成功色（清新绿）
        "warning": (251, 191, 36),  # 警告色（温暖黄）
        "danger": (239, 68, 68),  # 危险色（醒目红）
        "line": (96, 165, 250),  # 测量线颜色
        "line_label_bg": (12, 16, 24),  # 线标签背景
        "line_label_text": (255, 255, 255),  # 线标签文本
        "border": (64, 72, 88),  # 边框颜色
        "radar_fill": (36, 44, 58),  # 雷达图填充
        "radar_line": (64, 158, 255),  # 雷达图线条
        "radar_label": (240, 240, 245),  # 雷达图标签
        "hover_bg": (48, 56, 72),  # 悬停背景
        "shadow": (0, 0, 0),  # 阴影颜色
    }

    STAGE_LABELS = {
        "calibrating": "Step 1 校准中",
        "calibrated": "校准完成",
        "scanning": "Step 2 扫描中",
        "recommending": "Step 3 尺码推荐",
        "done": "Step 3 尺码推荐",
    }

    DISPLAY_MEASUREMENTS = [
        ("height", "身高"),
        ("shoulder", "肩宽"),
        ("chest", "胸围"),
        ("waist", "腰围"),
        ("hip", "臀围"),
    ]

    # 雷达图配置（用于体型分析）
    RADAR_DIMENSIONS = [
        ("height", "身高", 180, 150),   # (key, label, max_value, min_value)
        ("shoulder", "肩宽", 55, 35),
        ("chest", "胸围", 120, 75),
        ("waist", "腰围", 100, 60),
        ("hip", "臀围", 120, 80),
    ]

    # ========== 尺码推荐配置 ==========
    SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL", "3XL"]
    SIZE_FIT_OFFSETS = {
        "slim_fit": -1,
        "regular_fit": 0,
        "loose_fit": 1,
    }
    SIZE_RULES = {
        "XS": {
            "height": (150, 165),
            "chest": (78, 86),
            "waist": (64, 72),
            "hip": (80, 88),
            "shoulder": (36, 41),
        },
        "S": {
            "height": (155, 170),
            "chest": (84, 92),
            "waist": (70, 78),
            "hip": (86, 94),
            "shoulder": (38, 43),
        },
        "M": {
            "height": (160, 175),
            "chest": (90, 98),
            "waist": (76, 84),
            "hip": (92, 100),
            "shoulder": (40, 45),
        },
        "L": {
            "height": (165, 180),
            "chest": (96, 104),
            "waist": (82, 90),
            "hip": (98, 106),
            "shoulder": (42, 47),
        },
        "XL": {
            "height": (170, 185),
            "chest": (102, 110),
            "waist": (88, 96),
            "hip": (104, 112),
            "shoulder": (44, 49),
        },
        "XXL": {
            "height": (172, 190),
            "chest": (108, 116),
            "waist": (94, 102),
            "hip": (110, 118),
            "shoulder": (46, 51),
        },
        "3XL": {
            "height": (175, 195),
            "chest": (114, 124),
            "waist": (100, 110),
            "hip": (116, 126),
            "shoulder": (48, 54),
        },
    }

    # ========== 演示流程设置 ==========
    AUTO_EXIT_AFTER_MEASUREMENT = False  # 禁用自动退出，改为手动控制
    CALIBRATION_TIMEOUT_FRAMES = 600  # 延长校准超时时间
    ENABLE_DEMO_MODE = False  # 演示模式开关