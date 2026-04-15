class ConfigOptimized:
    # 摄像头设置 - 优化版本
    CAMERA_ID = 0
    CAMERA_WIDTH = 1920  # 提高分辨率到1080p
    CAMERA_HEIGHT = 1080
    CAMERA_FPS = 30
    
    # MediaPipe 设置 - 优化版本
    POSE_MIN_DETECTION_CONFIDENCE = 0.4  # 降低检测阈值，提高检测率
    POSE_MIN_TRACKING_CONFIDENCE = 0.4  # 降低跟踪阈值，提高稳定性
    POSE_MODEL_COMPLEXITY = 1  # 使用中等复杂度模型
    
    # 参照物设置 - 优化版本
    REFERENCE_OBJECTS = {
        "A4": {"width": 21.0, "min_area": 500, "max_area": 100000, "min_pixel": 50, "max_pixel": 500},
        "credit_card": {"width": 8.56, "min_area": 200, "max_area": 20000, "min_pixel": 30, "max_pixel": 200}
    }
    
    # 几何计算设置 - 优化版本
    HEIGHT_CORRECTION_FACTOR = 1.03  # 微调身高校正因子
    CHEST_CIRCUMFERENCE_FACTOR = 1.75  # 微调胸围经验系数
    
    # 滤波设置 - 优化版本
    FILTER_WINDOW_SIZE = 5  # 增加滤波窗口，提高稳定性
    
    # 可视化设置 - 优化版本
    SIDEBAR_WIDTH = 320
    FONT_SCALE = 0.8
    LINE_THICKNESS = 3
    
    # 尺码表 - 优化版本
    SIZE_CHART = {
        "S": {"chest": 90, "shoulder": 42, "height_range": (160, 170)},
        "M": {"chest": 100, "shoulder": 44, "height_range": (170, 180)},
        "L": {"chest": 110, "shoulder": 46, "height_range": (175, 185)},
        "XL": {"chest": 120, "shoulder": 48, "height_range": (180, 190)},
        "XXL": {"chest": 130, "shoulder": 50, "height_range": (185, 200)}
    }
    
    # 边缘检测参数 - 优化版本
    CANNY_THRESHOLD1 = 30  # 降低阈值
    CANNY_THRESHOLD2 = 100  # 降低阈值
    GAUSSIAN_KERNEL_SIZE = 3  # 使用更小的kernel
    
    # 轮廓近似参数 - 优化版本
    CONTOUR_APPROX_EPSILON = 0.03  # 增加近似误差
    
    # 参照物检测参数 - 优化版本
    MIN_CONTOUR_PERIMETER = 50  # 降低最小周长
    MIN_RECTANGULARITY = 0.5  # 降低最小矩形度
    MIN_ASPECT_RATIO = 0.5  # 扩大长宽比范围
    MAX_ASPECT_RATIO = 2.0  # 扩大长宽比范围
    
    # 检测评分阈值 - 优化版本
    MIN_DETECTION_SCORE = 3  # 降低检测得分阈值
    
    # 性能优化参数
    SKIP_FRAMES = 0  # 跳帧数（0=不跳帧，1=跳1帧）
    MAX_MEASUREMENTS = 10  # 最大测量次数
    MAX_CALIBRATION_ATTEMPTS = 50  # 最大校准尝试次数
    
    # 调试模式
    DEBUG_MODE = False  # 调试模式开关
    SHOW_INTERMEDIATE_RESULTS = False  # 显示中间结果
    
    # 质量控制
    MIN_MEASUREMENT_CONFIDENCE = 0.7  # 最小测量置信度
    MAX_MEASUREMENT_VARIANCE = 0.2  # 最大测量方差（20%）
