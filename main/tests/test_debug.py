import cv2
import sys
sys.path.append('.')

from src.utils.video_capture import VideoCapture
from src.config.config import Config

print("=== 调试摄像头 ===")

cap = VideoCapture(Config.CAMERA_ID)

try:
    print("打开摄像头...")
    cap.open()
    print("摄像头打开成功")
    
    # 读取 10 帧
    for i in range(10):
        print(f"读取第 {i+1} 帧...")
        frame = cap.read()
        
        if frame is None:
            print(f"第 {i+1} 帧：None")
            continue
            
        print(f"第 {i+1} 帧：shape={frame.shape}, size={frame.size}")
        
        # 显示帧
        cv2.imshow('Test', frame)
        cv2.waitKey(100)
    
    print("按任意键退出...")
    cv2.waitKey(0)
    
except Exception as e:
    print(f"错误：{e}")
    import traceback
    traceback.print_exc()
    
finally:
    cap.release()
    cv2.destroyAllWindows()
    print("完成")