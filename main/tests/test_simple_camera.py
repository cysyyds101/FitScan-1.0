import cv2
import time

# 简单测试
print("Testing camera with DirectShow...")
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    print("ERROR: Cannot open camera")
    exit()

print("Camera opened successfully")
time.sleep(1)

for i in range(3):
    ret, frame = cap.read()
    if ret:
        h, w, c = frame.shape
        print(f"Frame {i+1}: {w}x{h}")
    else:
        print(f"Frame {i+1}: Failed")

cap.release()
print("Done")