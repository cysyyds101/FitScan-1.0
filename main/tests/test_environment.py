import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import mediapipe as mp
import numpy as np

def test_camera():
    """测试摄像头是否正常"""
    print("测试摄像头...")
    try:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ 无法打开摄像头")
            return False
        
        ret, frame = cap.read()
        if not ret:
            print("❌ 无法读取摄像头画面")
            cap.release()
            return False
        
        print("✅ 摄像头测试通过")
        cap.release()
        return True
    except Exception as e:
        print(f"❌ 摄像头测试失败: {e}")
        return False

def test_mediapipe():
    """测试MediaPipe是否正常"""
    print("测试MediaPipe...")
    try:
        mp_pose = mp.solutions.pose
        pose = mp_pose.Pose()
        print("✅ MediaPipe测试通过")
        return True
    except Exception as e:
        print(f"❌ MediaPipe测试失败: {e}")
        return False

def test_opencv():
    """测试OpenCV是否正常"""
    print("测试OpenCV...")
    try:
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        print("✅ OpenCV测试通过")
        return True
    except Exception as e:
        print(f"❌ OpenCV测试失败: {e}")
        return False

def test_modules():
    """测试项目模块是否正常"""
    print("测试项目模块...")
    try:
        from src.core.reference_detector import ReferenceDetector
        from src.core.pose_estimator import PoseEstimator
        from src.core.geometry_calculator import GeometryCalculator
        from src.core.size_recommender import SizeRecommender
        from src.utils.visualizer import Visualizer
        from src.utils.video_capture import VideoCapture
        from src.config.config import Config
        
        print("✅ 项目模块测试通过")
        return True
    except Exception as e:
        print(f"❌ 项目模块测试失败: {e}")
        return False

def main():
    print("=" * 50)
    print("FitScan 环境测试")
    print("=" * 50)
    
    tests = [
        ("OpenCV", test_opencv),
        ("MediaPipe", test_mediapipe),
        ("摄像头", test_camera),
        ("项目模块", test_modules)
    ]
    
    all_passed = True
    for name, test_func in tests:
        print(f"\n测试 {name}...")
        if not test_func():
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 所有测试通过！")
        print("\n🚀 可以运行 main.py 开始使用FitScan了")
        print("   运行命令: python main.py")
    else:
        print("⚠️  部分测试失败，请检查环境配置")
        print("\n💡 解决方案:")
        print("   1. 确保已安装依赖: pip install -r requirements.txt")
        print("   2. 检查摄像头是否正常工作")
        print("   3. 确认Python版本 >= 3.7")
    print("=" * 50)

if __name__ == "__main__":
    main()