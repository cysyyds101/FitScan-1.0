import cv2
import sys

print("=== 摄像头诊断测试 ===")
print(f"OpenCV 版本：{cv2.__version__}")
print(f"Python 版本：{sys.version}")

# 列出所有可用的摄像头
print("\n=== 检测可用摄像头 ===")
for i in range(10):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret and frame is not None:
            h, w, _ = frame.shape
            print(f"摄像头 {i}: 可用 - 分辨率 {w}x{h}")
            cap.release()
        else:
            print(f"摄像头 {i}: 打开成功但无法读取帧")
            cap.release()
    else:
        print(f"摄像头 {i}: 不可用")

# 尝试使用 DirectShow
print("\n=== 尝试 DirectShow ===")
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if cap.isOpened():
    print("DirectShow 成功!")
    ret, frame = cap.read()
    if ret and frame is not None:
        print(f"帧大小：{frame.shape}")
        # 显示画面
        cv2.imshow('Test', frame)
        print("按任意键退出...")
        cv2.waitKey(0)
    cap.release()
else:
    print("DirectShow 失败")

print("\n测试完成")