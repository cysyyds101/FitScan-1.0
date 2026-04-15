import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.video_capture import VideoCapture
from src.core.reference_detector import ReferenceDetector
import time

def test_camera():
    print("=" * 50)
    print("摄像头测试")
    print("=" * 50)
    
    vc = VideoCapture(0)
    
    try:
        print("正在打开摄像头...")
        vc.open()
        print("摄像头打开成功!")
        
        # 测试读取多帧
        print("\n测试读取帧...")
        for i in range(5):
            frame = vc.read()
            if frame is not None:
                h, w, c = frame.shape
                print(f"  帧 {i+1}: 分辨率 {w}x{h}, 通道数 {c}")
            else:
                print(f"  帧 {i+1}: 读取失败")
        
        # 测试参照物检测
        print("\n测试参照物检测...")
        rd = ReferenceDetector()
        frame = vc.read()
        detected, result_frame = rd.detect(frame)
        print(f"  参照物检测结果：{detected}")
        
        print("\n测试完成!")
        
    except Exception as e:
        print(f"测试失败：{e}")
        import traceback
        traceback.print_exc()
    
    finally:
        vc.release()
        print("\n摄像头已释放")

if __name__ == "__main__":
    test_camera()