import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import argparse
import time
import traceback

import cv2

from src.config.config import Config
from src.core.geometry_calculator import GeometryCalculator
from src.core.pose_estimator import PoseEstimator
from src.core.reference_detector import ReferenceDetector
from src.core.size_recommender import SizeRecommender
from src.utils.video_capture import VideoCapture
from src.utils.visualizer import Visualizer


class FitScanApp:
    def __init__(self):
        self.video_capture = VideoCapture(Config.CAMERA_ID)
        self.reference_detector = ReferenceDetector()
        self.pose_estimator = PoseEstimator()
        self.geometry_calculator = GeometryCalculator()
        self.size_recommender = SizeRecommender()
        self.visualizer = Visualizer()

        self.is_calibrated = False
        self.measurements = {}
        self.recommended_size = None
        self.window_locked = False
        self.initial_window_size = (1280, 720)

        self.stage_key = "calibrating"
        self.latest_scale_factor = None
        self.latest_reference_object = None
        self.report_generated = False
        self.report_printed = False

    def initialize(self):
        try:
            print("正在初始化摄像头...")
            self.video_capture.open()
            print("摄像头打开成功")

            test_frame = self.video_capture.read()
            if test_frame is not None:
                h, w, _ = test_frame.shape
                print(f"摄像头分辨率：{w}x{h}")
            else:
                print("无法读取摄像头帧")
                return False

            print("使用摄像头默认分辨率")
            print("初始化成功")
            return True
        except Exception as e:
            print(f"初始化失败：{e}")
            traceback.print_exc()
            return False

    def _draw_overlay_text(self, frame, lines, color=(255, 255, 255)):
        if frame is None:
            return frame

        y = 30
        for line in lines:
            cv2.putText(
                frame,
                line,
                (12, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 0, 0),
                4,
                cv2.LINE_AA,
            )
            cv2.putText(
                frame,
                line,
                (12, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                color,
                2,
                cv2.LINE_AA,
            )
            y += 30
        return frame

    def _draw_measurement_annotations(self, frame, landmarks):
        if not landmarks or not self.measurements:
            return frame

        h, w = frame.shape[:2]

        if len(landmarks) > 12 and "shoulder" in self.measurements:
            left_shoulder = (int(landmarks[11].x * w), int(landmarks[11].y * h))
            right_shoulder = (int(landmarks[12].x * w), int(landmarks[12].y * h))
            frame = self.visualizer.draw_measurement_line(
                frame,
                left_shoulder,
                right_shoulder,
                f"肩宽 {self.measurements['shoulder']:.1f}cm",
                color=(70, 200, 120),
            )

        if len(landmarks) > 15 and "arm_left" in self.measurements:
            left_shoulder = (int(landmarks[11].x * w), int(landmarks[11].y * h))
            left_wrist = (int(landmarks[15].x * w), int(landmarks[15].y * h))
            frame = self.visualizer.draw_measurement_line(
                frame,
                left_shoulder,
                left_wrist,
                f"左臂 {self.measurements['arm_left']:.1f}cm",
                color=(83, 172, 255),
            )

        if len(landmarks) > 16 and "arm_right" in self.measurements:
            right_shoulder = (int(landmarks[12].x * w), int(landmarks[12].y * h))
            right_wrist = (int(landmarks[16].x * w), int(landmarks[16].y * h))
            frame = self.visualizer.draw_measurement_line(
                frame,
                right_shoulder,
                right_wrist,
                f"右臂 {self.measurements['arm_right']:.1f}cm",
                color=(83, 172, 255),
            )

        if len(landmarks) > 27 and "leg_left" in self.measurements:
            left_hip = (int(landmarks[23].x * w), int(landmarks[23].y * h))
            left_ankle = (int(landmarks[27].x * w), int(landmarks[27].y * h))
            frame = self.visualizer.draw_measurement_line(
                frame,
                left_hip,
                left_ankle,
                f"左腿 {self.measurements['leg_left']:.1f}cm",
                color=(255, 196, 87),
            )

        if len(landmarks) > 28 and "leg_right" in self.measurements:
            right_hip = (int(landmarks[24].x * w), int(landmarks[24].y * h))
            right_ankle = (int(landmarks[28].x * w), int(landmarks[28].y * h))
            frame = self.visualizer.draw_measurement_line(
                frame,
                right_hip,
                right_ankle,
                f"右腿 {self.measurements['leg_right']:.1f}cm",
                color=(255, 196, 87),
            )

        if len(landmarks) > 28 and "height" in self.measurements:
            nose = (int(landmarks[0].x * w), int(landmarks[0].y * h))
            avg_ankle = (
                int(((landmarks[27].x + landmarks[28].x) / 2) * w),
                int(((landmarks[27].y + landmarks[28].y) / 2) * h),
            )
            frame = self.visualizer.draw_measurement_line(
                frame,
                nose,
                avg_ankle,
                f"身高 {self.measurements['height']:.1f}cm",
                color=(255, 107, 107),
            )

        return frame

    def _print_report(self):
        if self.report_printed or not self.measurements:
            return

        recommendation = self.recommended_size or {}
        print("\n" + "=" * 56)
        print("              FitScan 智能量体报告")
        print("=" * 56)
        print(f"阶段：{Config.STAGE_LABELS.get(self.stage_key, self.stage_key)}")
        if self.latest_reference_object:
            ref = Config.REFERENCE_OBJECTS.get(self.latest_reference_object, {})
            ref_label = ref.get("label", self.latest_reference_object)
            print(f"参照物：{ref_label}")
        if self.latest_scale_factor:
            print(f"比例系数 K：{self.latest_scale_factor:.4f} cm/px")

        print("\n【核心尺寸】")
        for key, label in [("height", "身高"), ("shoulder", "肩宽"), ("chest", "胸围"), ("waist", "腰围"), ("hip", "臀围")]:
            if key in self.measurements:
                suffix = "（估算）" if key in {"height", "chest", "waist", "hip"} else ""
                print(f"  {label}{suffix}：{self.measurements[key]:.2f} cm")

        print("\n【直接测量项】")
        for key, label in [
            ("arm_left", "左臂全长"),
            ("arm_right", "右臂全长"),
            ("leg_left", "左腿全长"),
            ("leg_right", "右腿全长"),
            ("hip_width", "臀宽"),
        ]:
            if key in self.measurements:
                print(f"  {label}：{self.measurements[key]:.2f} cm")

        print("\n【估算项】")
        for key, label in [("waist_width", "腰宽"), ("neck", "颈围")]:
            if key in self.measurements:
                print(f"  {label}：{self.measurements[key]:.2f} cm")

        print("\n【尺码建议】")
        if isinstance(recommendation, dict):
            print(f"  主推荐：{recommendation.get('primary', '--')}")
            print(f"  修身版：{recommendation.get('slim_fit', '--')}")
            print(f"  常规版：{recommendation.get('regular_fit', '--')}")
            print(f"  宽松版：{recommendation.get('loose_fit', '--')}")
        elif recommendation:
            print(f"  推荐尺码：{recommendation}")

        print("\n按键说明：q 退出 | r 重新校准 | s 锁定并生成建议 | c 返回扫描")
        print("=" * 56)
        self.report_printed = True

    def run(self, no_gui=False):
        try:
            if not self.initialize():
                return

            print("FitScan started successfully!")
            print("请先将 A4 纸、身份证或银行卡放在胸前完成校准。")
            print("校准成功后自然站立，按 s 锁定当前结果并生成尺码建议。")

            calibration_count = 0
            window_initialized = False

            while True:
                frame = self.video_capture.read()

                if frame is None or frame.size == 0:
                    print("Warning: 无法读取摄像头帧，跳过此帧")
                    continue

                if len(frame.shape) != 3:
                    print("Warning: 无效的帧格式")
                    continue

                h, w, _ = frame.shape

                if not self.is_calibrated:
                    self.stage_key = "calibrating"
                    detected, detected_frame = self.reference_detector.detect(frame)
                    frame = detected_frame if detected_frame is not None else frame
                    scale_factor = self.reference_detector.get_scale_factor() if detected else None
                    reference_object = self.reference_detector.get_detected_object() if detected else None

                    overlay_lines = [
                        Config.STAGE_LABELS.get("calibrating", "Step 1 校准中"),
                        "请将参照物贴近胸前，与身体尽量保持同一平面",
                    ]

                    if detected:
                        self.is_calibrated = True
                        self.latest_scale_factor = scale_factor
                        self.latest_reference_object = reference_object
                        print(f"校准成功：{reference_object} | K={scale_factor:.4f} cm/px")
                        print("进入扫描阶段，请自然站立并微微张开双臂。")
                    else:
                        calibration_count += 1
                        if calibration_count >= Config.CALIBRATION_TIMEOUT_FRAMES:
                            print("Calibration timeout. Exiting...")
                            break

                    frame = self._draw_overlay_text(frame, overlay_lines, color=(70, 200, 120))
                    frame = self.visualizer.draw_sidebar(
                        frame,
                        self.measurements,
                        self.recommended_size,
                        scale_factor,
                        stage_key="calibrating",
                        reference_object=reference_object,
                    )
                else:
                    try:
                        results = self.pose_estimator.process(frame)

                        if results.pose_landmarks:
                            frame = self.pose_estimator.draw_landmarks(frame, results)
                            landmarks = self.pose_estimator.get_keypoints(results)
                            filtered_landmarks = self.pose_estimator.apply_filter(landmarks)

                            scale_factor = self.reference_detector.get_scale_factor()
                            self.latest_scale_factor = scale_factor
                            self.latest_reference_object = self.reference_detector.get_detected_object()

                            self.measurements = self.geometry_calculator.calculate_all_measurements(
                                filtered_landmarks,
                                scale_factor,
                                w,
                                h,
                            )

                            if Config.ENABLE_MULTI_FRAME_AVERAGE:
                                self.measurements = self.geometry_calculator.get_averaged_measurements()

                            if self.report_generated:
                                self.stage_key = "recommending"
                                self.recommended_size = self.size_recommender.recommend(self.measurements)
                            else:
                                self.stage_key = "scanning"
                                self.recommended_size = self.size_recommender.recommend(self.measurements)

                            frame = self._draw_measurement_annotations(frame, filtered_landmarks)
                            frame = self._draw_overlay_text(
                                frame,
                                [
                                    Config.STAGE_LABELS.get(self.stage_key, self.stage_key),
                                    "按 s 锁定当前结果并生成尺码建议",
                                    "按 r 重新校准，按 q 退出",
                                ],
                                color=(255, 255, 255),
                            )
                            frame = self.visualizer.draw_sidebar(
                                frame,
                                self.measurements,
                                self.recommended_size,
                                scale_factor,
                                stage_key=self.stage_key,
                                reference_object=self.latest_reference_object,
                            )

                            if self.report_generated:
                                self._print_report()
                                if Config.AUTO_EXIT_AFTER_MEASUREMENT:
                                    print("Measurement completed. Exiting...")
                                    break
                        else:
                            self.stage_key = "scanning"
                            frame = self._draw_overlay_text(
                                frame,
                                [
                                    Config.STAGE_LABELS.get("scanning", "Step 2 扫描中"),
                                    "请站在摄像头前，保持完整上半身和腿部在画面中",
                                ],
                                color=(255, 196, 87),
                            )
                            frame = self.visualizer.draw_sidebar(
                                frame,
                                self.measurements,
                                self.recommended_size,
                                self.latest_scale_factor,
                                stage_key="scanning",
                                reference_object=self.latest_reference_object,
                            )
                    except Exception as e:
                        print(f"Processing error: {e}")
                        traceback.print_exc()
                        continue

                if not no_gui:
                    if not window_initialized:
                        cv2.namedWindow("FitScan", cv2.WINDOW_NORMAL)
                        cv2.resizeWindow("FitScan", self.initial_window_size[0], self.initial_window_size[1])
                        window_initialized = True

                    cv2.imshow("FitScan", frame)
                    key = cv2.waitKey(1) & 0xFF

                    # 检查窗口是否被关闭
                    try:
                        window_property = cv2.getWindowProperty("FitScan", cv2.WND_PROP_VISIBLE)
                        if window_property < 1:
                            print("Window closed by user...")
                            break
                    except Exception as e:
                        print(f"检查窗口状态时出错: {e}")
                        # 如果无法获取窗口属性，可能窗口已经关闭
                        break

                    if key == ord("q"):
                        print("User exited...")
                        break
                    elif key == ord("r"):
                        self.reset_calibration()
                        calibration_count = 0
                        print("重新校准中...")
                    elif key == ord("s") and self.is_calibrated and self.measurements:
                        self.report_generated = True
                        self.report_printed = False
                        self.stage_key = "recommending"
                        print("已锁定当前测量结果，正在生成尺码建议...")
                    elif key == ord("c") and self.is_calibrated:
                        self.report_generated = False
                        self.report_printed = False
                        self.stage_key = "scanning"
                        print("已返回扫描模式。")
                    elif key == ord("p"):
                        self.window_locked = not self.window_locked
                        status = "已锁定" if self.window_locked else "已解锁"
                        print(f"窗口大小{status} (按'p'切换)")
                        if self.window_locked:
                            cv2.resizeWindow("FitScan", self.initial_window_size[0], self.initial_window_size[1])
                else:
                    time.sleep(0.1)

        finally:
            print("Cleaning up resources...")
            self.cleanup()

    def reset_calibration(self):
        self.is_calibrated = False
        self.reference_detector.reset()
        self.geometry_calculator.reset()
        self.measurements = {}
        self.recommended_size = None
        self.latest_scale_factor = None
        self.latest_reference_object = None
        self.stage_key = "calibrating"
        self.report_generated = False
        self.report_printed = False

    def cleanup(self):
        try:
            self.video_capture.release()
            print("摄像头资源已释放")
        except Exception as e:
            print(f"释放摄像头失败：{e}")

        try:
            self.pose_estimator.cleanup()
            print("姿态估计器已关闭")
        except Exception as e:
            print(f"关闭姿态估计器失败：{e}")

        try:
            cv2.destroyAllWindows()
            cv2.waitKey(1)
            print("OpenCV 窗口已关闭")
        except Exception as e:
            print(f"关闭窗口失败：{e}")

        print("FitScan 已关闭")


def main():
    parser = argparse.ArgumentParser(description="FitScan - 智能人体尺寸估算系统")
    parser.add_argument("--no-gui", action="store_true", help="不显示 GUI 窗口，仅输出结果")
    args = parser.parse_args()

    app = FitScanApp()
    app.run(no_gui=args.no_gui)


if __name__ == "__main__":
    main()
