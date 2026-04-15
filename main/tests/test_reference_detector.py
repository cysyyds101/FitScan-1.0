import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
from src.core.reference_detector import ReferenceDetector

def test_reference_detector():
    """测试参照物检测功能"""
    print("测试参照物检测...")
    
    # 初始化检测器
    detector = ReferenceDetector()
    
    # 打开摄像头
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ 无法打开摄像头")
        return False
    
    print("📷 摄像头已打开，请将A4纸或银行卡放在画面中")
    print("按 'q' 退出测试")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # 检测参照物
        detected, frame = detector.detect(frame)
        
        # 显示提示信息
        cv2.putText(frame, "测试模式: 请将A4纸或银行卡放在画面中", 
                   (10, frame.shape[0]-30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # 显示画面
        cv2.imshow('Reference Detector Test', frame)
        
        # 按 'q' 退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    # 检查是否检测到参照物
    if detector.get_detected_object():
        print(f"✅ 成功检测到: {detector.get_detected_object()}")
        print(f"✅ 比例系数: {detector.get_scale_factor():.4f} cm/px")
        return True
    else:
        print("❌ 未检测到参照物")
        return False

def main():
    print("=" * 60)
    print("FitScan 参照物检测测试")
    print("=" * 60)
    
    test_result = test_reference_detector()
    
    print("\n" + "=" * 60)
    if test_result:
        print("🎉 参照物检测测试通过！")
    else:
        print("⚠️  参照物检测测试失败")
        print("\n💡 建议:")
        print("   1. 确保光线充足")
        print("   2. 确保参照物清晰可见")
        print("   3. 调整摄像头角度")
        print("   4. 确保背景简洁")
    print("=" * 60)

if __name__ == "__main__":
    main()