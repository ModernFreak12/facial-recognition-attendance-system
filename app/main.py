import cv2
from pathlib import Path
from datetime import datetime

from app.config import WEIGHTS_PATH, CONF, IOU, IMG_SIZE, DEVICE, CAM_INDEX, SHOW_FPS, WINDOW_NAME
from app.detection.face_detector import FaceDetector
from app.utils.video import open_camera, release_camera, FPS
from app.utils.drawing import draw_detections


def main():
    print(f"[i] Using weights: {Path(WEIGHTS_PATH).resolve()}")
    detector = FaceDetector(Path(WEIGHTS_PATH), device=DEVICE, conf=CONF, iou=IOU, img_size=IMG_SIZE)
    print("[i] Model loaded ✅")

    cap = open_camera(CAM_INDEX, width=640, height=480)
    fps = FPS()

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    print("[i] Live preview ready — press 's' to capture & detect, 'q' to quit.")

    # Create detections folder (auto)
    save_dir = Path("detections")
    save_dir.mkdir(exist_ok=True)

    last_vis = None
    show_detection_frames = 0

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("[!] Failed to read frame.")
                break

            # Flip horizontally (mirror view)
            frame = cv2.flip(frame, 1)

            # Show detection result for a few frames if exists
            if last_vis is not None and show_detection_frames > 0:
                display = last_vis
                show_detection_frames -= 1
            else:
                display = frame

            # Optional FPS overlay
            if SHOW_FPS:
                fps.tick()
                cv2.putText(display, f"FPS: {fps.value:.1f}", (10, 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3)
                cv2.putText(display, f"FPS: {fps.value:.1f}", (10, 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

            cv2.imshow(WINDOW_NAME, display)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

            elif key == ord('s'):
                # Capture & detect on the CURRENT flipped frame
                from datetime import datetime
                import time, traceback
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_dir = Path("detections"); save_dir.mkdir(exist_ok=True)
                raw_path = save_dir / f"raw_{timestamp}.jpg"
                det_path = save_dir / f"det_{timestamp}.jpg"

                # Save raw frame first so you always have evidence
                cv2.imwrite(str(raw_path), frame)
                print(f"\n[i] Captured frame at {timestamp}. Saved raw → {raw_path.resolve()}")
                print("[i] Running detection...")

                # Time the predict call
                dets = []
                try:
                    t0 = time.perf_counter()
                    dets = detector.predict(frame)
                    dt_ms = (time.perf_counter() - t0) * 1000
                    print(f"[i] Detection OK: {len(dets)} boxes in {dt_ms:.1f} ms")
                except Exception:
                    print("🔥 YOLO predict error:")
                    traceback.print_exc()

                # Draw (no confidence) and save annotated
                vis = draw_detections(frame.copy(), dets, show_label=True, show_conf=False)
                cv2.imwrite(str(det_path), vis)
                print(f"[i] Saved annotated → {det_path.resolve()}")

                # Show annotated for ~1.5s so you SEE it worked
                show_detection_frames = 45
                last_vis = vis


    finally:
        release_camera(cap)
        print("[i] Camera released and window closed ✅")


if __name__ == "__main__":
    main()
