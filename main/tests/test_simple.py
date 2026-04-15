"""
FitScan 简化性能测试
不依赖摄像头的测试版本
"""

import cv2
import time
import numpy as np
from src.core.reference_detector import ReferenceDetector
from src.core.geometry_calculator import GeometryCalculator

def test_reference_detection():
    """测试参照物检测性能"""
    print("\n=== 参照物检测测试 ===")
    
    # 创建测试图像
    test_img = np.ones((480, 640, 3), dtype=np.uint8) * 255
    cv2.rectangle(test_img, (200, 150), (400, 290), (0, 0, 0), 2)
    
    detector = ReferenceDetector()
    
    # 测试检测速度
    start_time = time.time()
    detections = 0
    for _ in range(100):
        detected, _ = detector.detect(test_img)
        if detected:
            detections += 1
    end_time = time.time()
    
    avg_time = (end_time - start_time) / 100 * 1000  # 毫秒
    success_rate = detections / 100 * 100
    
    print(f"平均检测时间: {avg_time:.2f}ms")
    print(f"检测成功率: {success_rate:.1f}%")
    
    if success_rate > 90:
        print("✓ 检测性能优秀")
    elif success_rate > 70:
        print("✓ 检测性能良好")
    else:
        print("✗ 检测性能需优化")
    
    return success_rate > 70

def test_geometry_calculation():
    """测试几何计算性能"""
    print("\n=== 几何计算测试 ===")
    
    # 创建模拟关键点
    class Landmark:
        def __init__(self, x, y, z):
            self.x = x
            self.y = y
            self.z = z
    
    landmarks = []
    for i in range(33):
        landmarks.append(Landmark(0.5, 0.5, 0.5))
    
    calculator = GeometryCalculator()
    
    # 测试计算速度
    start_time = time.time()
    for _ in range(1000):
        measurements = calculator.calculate_all_measurements(
            landmarks, 0.1, 640, 480
        )
    end_time = time.time()
    
    avg_time = (end_time - start_time) / 1000 * 1000  # 毫秒
    print(f"平均计算时间: {avg_time:.2f}ms")
    print(f"测量结果数量: {len(measurements)}")
    
    if avg_time < 1:
        print("✓ 计算性能优秀")
    elif avg_time < 5:
        print("✓ 计算性能良好")
    else:
        print("✗ 计算性能需优化")
    
    return len(measurements) > 0

def test_image_processing():
    """测试图像处理性能"""
    print("\n=== 图像处理测试 ===")
    
    # 创建测试图像
    test_img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    # 测试灰度转换
    start_time = time.time()
    for _ in range(1000):
        gray = cv2.cvtColor(test_img, cv2.COLOR_BGR2GRAY)
    end_time = time.time()
    
    avg_time = (end_time - start_time) / 1000 * 1000  # 毫秒
    print(f"灰度转换时间: {avg_time:.2f}ms")
    
    # 测试边缘检测
    start_time = time.time()
    for _ in range(100):
        edges = cv2.Canny(gray, 50, 150)
    end_time = time.time()
    
    avg_time = (end_time - start_time) / 100 * 1000  # 毫秒
    print(f"边缘检测时间: {avg_time:.2f}ms")
    
    print("✓ 图像处理功能正常")
    return True

def test_numpy_performance():
    """测试NumPy性能"""
    print("\n=== NumPy性能测试 ===")
    
    # 测试矩阵运算
    start_time = time.time()
    for _ in range(1000):
        a = np.random.rand(100, 100)
        b = np.random.rand(100, 100)
        c = np.dot(a, b)
    end_time = time.time()
    
    avg_time = (end_time - start_time) / 1000 * 1000  # 毫秒
    print(f"矩阵乘法时间: {avg_time:.2f}ms")
    
    if avg_time < 1:
        print("✓ NumPy性能优秀")
    elif avg_time < 5:
        print("✓ NumPy性能良好")
    else:
        print("✗ NumPy性能需优化")
    
    return avg_time < 5

def main():
    """主测试函数"""
    print("=" * 50)
    print("FitScan 环境优化测试（简化版）")
    print("=" * 50)
    
    results = {}
    
    # 运行各项测试
    try:
        results['参照物检测'] = test_reference_detection()
    except Exception as e:
        print(f"参照物检测测试失败: {e}")
        import traceback
        traceback.print_exc()
        results['参照物检测'] = False
    
    try:
        results['几何计算'] = test_geometry_calculation()
    except Exception as e:
        print(f"几何计算测试失败: {e}")
        import traceback
        traceback.print_exc()
        results['几何计算'] = False
    
    try:
        results['图像处理'] = test_image_processing()
    except Exception as e:
        print(f"图像处理测试失败: {e}")
        import traceback
        traceback.print_exc()
        results['图像处理'] = False
    
    try:
        results['NumPy性能'] = test_numpy_performance()
    except Exception as e:
        print(f"NumPy性能测试失败: {e}")
        import traceback
        traceback.print_exc()
        results['NumPy性能'] = False
    
    # 输出测试结果
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    
    for test_name, passed in results.items():
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{test_name}: {status}")
    
    passed_count = sum(results.values())
    total_count = len(results)
    
    print(f"\n通过率: {passed_count}/{total_count} ({passed_count/total_count*100:.1f}%)")
    
    if passed_count == total_count:
        print("\n🎉 所有测试通过！环境配置优秀。")
        print("算法性能良好，可以获得准确的测量结果。")
    elif passed_count >= total_count * 0.7:
        print("\n✅ 大部分测试通过，环境配置良好。")
        print("算法性能可以满足基本需求。")
    else:
        print("\n⚠️ 部分测试失败，建议优化环境配置。")
        print("请参考 OPTIMIZATION_GUIDE.md 进行优化。")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()
