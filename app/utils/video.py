import time
import cv2


class FPS:
    def __init__(self, avg_over=30):
        self.t = time.time()
        self.buf = []
        self.avg_over = avg_over

    def tick(self):
        now = time.time()
        fps = 1.0 / max(1e-9, (now - self.t))
        self.t = now
        self.buf.append(fps)
        if len(self.buf) > self.avg_over:
            self.buf.pop(0)

    @property
    def value(self):
        return sum(self.buf) / len(self.buf) if self.buf else 0.0


def open_camera(index=0, width=None, height=None):
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)  # CAP_DSHOW helps on Windows
    if width:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    if height:
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open camera index {index}")
    return cap


def release_camera(cap):
    try:
        cap.release()
    finally:
        cv2.destroyAllWindows()
