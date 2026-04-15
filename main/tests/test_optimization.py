"""
FitScan 优化效果测试脚本
用于验证环境优化后的性能提升
"""

import cv2
import time
import numpy as np
from src.core.reference_detector import ReferenceDetector
from src.core.pose_estimator import PoseEstimator
from src.core.geometry_calculator import GeometryCalculator
from src.utils.video_capture import VideoCapture
from src.config.config import Config

def test_reference_detection():
    """测试参照物检测性能"""
    print("\n=== 参照物检测测试 ===")
    
    # 创建测试图像
    test_img = np.ones((480, 640, 3), dtype=np.uint8) * 255
    cv2.rectangle(test_img, (200, 150), (400, 290), (0, 0, 0), 2)
    
    detector = ReferenceDetector()
    
    # 测试检测速度
    start_time = time.time()
    for _ in range(100):
        detected, _ = detector.detect(test_img)
    end_time = time.time()
    
    avg_time = (end_time - start_time) / 100 * 1000  # 毫秒
    print(f"平均检测时间: {avg_time:.2f}ms")
    print(f"检测成功率: {'成功' if detected else '失败'}")
    
    return detected

def test_pose_estimation():
    """测试姿态估计性能"""
    print("\n=== 姿态估计测试 ===")
    
    # 打开摄像头
    cap = VideoCapture(Config.CAMERA_ID)
    try:
        cap.open()
        pose_estimator = PoseEstimator()
        
        # 读取测试帧
        frame = cap.read()
        
        # 测试姿态估计速度
        start_time = time.time()
        for _ in range(30):
            results = pose_estimator.process(frame)
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 30 * 1000  # 毫秒
        fps = 1000 / avg_time
        
        print(f"平均处理时间: {avg_time:.2f}ms")
        print(f"理论帧率: {fps:.1f}fps")
        print(f"检测到人体: {'是' if results.pose_landmarks else '否'}")
        
        return fps > 10  # 目标帧率 > 10fps
        
    finally:
        cap.release()

def test_geometry_calculation():
    """测试几何计算性能"""
    print("\n=== 几何计算测试 ===")
    
    # 创建模拟关键点
    landmarks = []
    for i in range(33):
        class Landmark:
            def __init__(self, x, y, z):
                self.x = x
                self.y = y
                self.z = z
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
    
    return len(measurements) > 0

def test_camera_performance():
    """测试摄像头性能"""
    print("\n=== 摄像头性能测试 ===")
    
    cap = VideoCapture(Config.CAMERA_ID)
    try:
        cap.open()
        
        # 测试帧率
        frame_count = 0
        start_time = time.time()
        test_duration = 3  # 测试3秒
        
        while time.time() - start_time < test_duration:
            frame = cap.read()
            if frame is not None:
                frame_count += 1
        
        actual_fps = frame_count / test_duration
        print(f"实际帧率: {actual_fps:.1f}fps")
        print(f"总帧数: {frame_count}")
        
        # 获取摄像头信息
        if frame is not None:
            h, w, _ = frame.shape
            print(f"分辨率: {w}x{h}")
        
        return actual_fps > 15  # 目标帧率 > 15fps
        
    finally:
        cap.release()

def test_overall_performance():
    """综合性能测试"""
    print("\n=== 综合性能测试 ===")
    print("开始完整流程测试...")
    
    cap = VideoCapture(Config.CAMERA_ID)
    try:
        cap.open()
        
        detector = ReferenceDetector()
        pose_estimator = PoseEstimator()
        calculator = GeometryCalculator()
        
        # 测试完整流程
        frame_count = 0
        start_time = time.time()
        test_duration = 5  # 测试5秒
        
        while time.time() - start_time < test_duration:
            frame = cap.read()
            if frame is None:
                continue
            
            frame_count += 1
            
            # 参照物检测
            detected, frame = detector.detect(frame)
            
            # 姿态估计
            results = pose_estimator.process(frame)
            
            if results.pose_landmarks:
                # 获取关键点
                landmarks = pose_estimator.get_keypoints(results)
                
                # 计算尺寸
                if detected:
                    scale_factor = detector.get_scale_factor()
                    measurements = calculator.calculate_all_measurements(
                        landmarks, scale_factor, 640, 480
                    )
        
        end_time = time.time()
        avg_fps = frame_count / (end_time - start_time)
        
        print(f"平均帧率: {avg_fps:.1f}fps")
        print(f"总处理帧数: {frame_count}")
        print(f"性能评级: {'优秀' if avg_fps > 20 else '良好' if avg_fps > 10 else '需优化'}")
        
        return avg_fps > 10  # 目标帧率 > 10fps
        
    finally:
        cap.release()

def main():
    """主测试函数"""
    print("=" * 50)
    print("FitScan 环境优化测试")
    print("=" * 50)
    
    results = {}
    
    # 运行各项测试
    try:
        results['参照物检测'] = test_reference_detection()
    except Exception as e:
        print(f"参照物检测测试失败: {e}")
        results['参照物检测'] = False
    
    try:
        results['姿态估计'] = test_pose_estimation()
    except Exception as e:
        print(f"姿态估计测试失败: {e}")
        results['姿态估计'] = False
    
    try:
        results['几何计算'] = test_geometry_calculation()
    except Exception as e:
        print(f"几何计算测试失败: {e}")
        results['几何计算'] = False
    
    try:
        results['摄像头性能'] = test_camera_performance()
    except Exception as e:
        print(f"摄像头性能测试失败: {e}")
        results['摄像头性能'] = False
    
    try:
        results['综合性能'] = test_overall_performance()
    except Exception as e:
        print(f"综合性能测试失败: {e}")
        results['综合性能'] = False
    
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
    elif passed_count >= total_count * 0.7:
        print("\n✅ 大部分测试通过，环境配置良好。")
    else:
        print("\n⚠️ 部分测试失败，建议优化环境配置。")

if __name__ == "__main__":
    main()
