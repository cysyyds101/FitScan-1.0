import cv2
import numpy as np
from src.core.reference_detector import ReferenceDetector

# 创建测试图像 - 模拟A4纸
img = np.ones((480, 640, 3), dtype=np.uint8) * 255

# 在图像中央绘制一个矩形模拟A4纸
x, y, w, h = 200, 150, 200, 140  # A4纸的近似比例
cv2.rectangle(img, (x, y), (x+w, y+h), (0, 0, 0), 2)

# 保存测试图像
cv2.imwrite('test_a4.jpg', img)
print("测试图像已创建: test_a4.jpg")

# 测试参照物检测
detector = ReferenceDetector()
detected, result = detector.detect(img)

if detected:
    scale_factor = detector.get_scale_factor()
    detected_obj = detector.get_detected_object()
    print(f"检测成功! 物体: {detected_obj}, 比例因子: {scale_factor:.4f} cm/px")
else:
    print("检测失败")

# 显示结果
cv2.imwrite('test_result.jpg', result)
print("检测结果已保存: test_result.jpg")
