import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.video_capture import VideoCapture
from src.core.reference_detector import ReferenceDetector
from src.core.pose_estimator import PoseEstimator
from src.core.geometry_calculator import GeometryCalculator
from src.core.size_recommender import SizeRecommender
import time

def test_full():
    print("=" * 50)
    print("完整系统测试")
    print("=" * 50)
    
    try:
        # 初始化摄像头
        print("\n1. 初始化摄像头...")
        vc = VideoCapture(0)
        vc.open()
        print("   摄像头打开成功!")
        
        # 测试读取帧
        print("\n2. 测试读取帧...")
        frame = vc.read()
        h, w, c = frame.shape
        print(f"   分辨率：{w}x{h}")
        
        # 测试参照物检测
        print("\n3. 测试参照物检测...")
        rd = ReferenceDetector()
        detected, result_frame = rd.detect(frame)
        print(f"   参照物检测结果：{detected}")
        
        # 测试姿态估计
        print("\n4. 测试姿态估计...")
        pe = PoseEstimator()
        results = pe.process(frame)
        has_landmarks = results.pose_landmarks is not None
        print(f"   姿态检测结果：{'检测到人体' if has_landmarks else '未检测到人体'}")
        
        # 测试几何计算
        print("\n5. 测试几何计算...")
        gc = GeometryCalculator()
        if has_landmarks:
            keypoints = pe.get_keypoints(results)
            scale = 0.004  # 模拟比例因子
            measurements = gc.calculate_all_measurements(keypoints, scale, w, h)
            print(f"   测量项目数：{len(measurements)}")
            for name, value in measurements.items():
                print(f"     {name}: {value:.2f} cm")
        else:
            print("   跳过（未检测到人体）")
        
        # 测试尺码推荐
        print("\n6. 测试尺码推荐...")
        sr = SizeRecommender()
        if has_landmarks:
            recommended = sr.recommend(measurements)
            print(f"   推荐尺码：{recommended}")
        else:
            print("   跳过（未检测到人体）")
        
        print("\n" + "=" * 50)
        print("测试完成!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n测试失败：{e}")
        import traceback
        traceback.print_exc()
    
    finally:
        vc.release()
        print("\n摄像头已释放")

if __name__ == "__main__":
    test_full()