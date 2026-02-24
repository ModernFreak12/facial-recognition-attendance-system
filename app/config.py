import os
from pathlib import Path


# -------------------------------------------------------------
# ROOT PATHS
# -------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]

MODELS_DIR = ROOT / "models"
FD_DIR     = MODELS_DIR / "face_detection"
FR_DIR     = MODELS_DIR / "face_recognition"
LM_DIR     = MODELS_DIR / "face_landmarks"       # NEW


# -------------------------------------------------------------
# INTERNAL HELPERS
# -------------------------------------------------------------
def _latest(paths):
    """Return newest file among given paths."""
    paths = [p for p in paths if p.exists()]
    return max(paths, key=lambda p: p.stat().st_mtime) if paths else None


def _auto_weights() -> Path:
    """
    Auto-detect YOLO model weights for face detection.
    Priority:
        1) best*.pt under models/face_detection/runs/**/weights/
        2) any .pt under models/face_detection/
        3) any .pt under models/
    """
    # 1) best*.pt in YOLO runs
    best = _latest(FD_DIR.glob("runs/**/weights/best*.pt"))
    if best:
        return best

    # 2) any .pt inside face_detection root
    any_fd = _latest(FD_DIR.glob("*.pt"))
    if any_fd:
        return any_fd

    # 3) any .pt in top-level models dir
    any_models = _latest(MODELS_DIR.glob("*.pt"))
    if any_models:
        return any_models

    raise FileNotFoundError("No YOLO .pt weights found.")


# -------------------------------------------------------------
# YOLO DETECTOR CONFIG
# -------------------------------------------------------------
# Allow override via environment variable
WEIGHTS_PATH = Path(os.getenv("WEIGHTS_PATH", _auto_weights()))

CONF     = float(os.getenv("CONF", "0.6"))
IOU      = float(os.getenv("IOU", "0.5"))
IMG_SIZE = int(os.getenv("IMG_SIZE", "2208"))
DEVICE   = os.getenv("DEVICE", "cpu")      # "cpu" or "cuda"


# -------------------------------------------------------------
# CAMERA / WINDOW CONFIG
# -------------------------------------------------------------
CAM_INDEX   = int(os.getenv("CAM_INDEX", "0"))
SHOW_FPS    = os.getenv("SHOW_FPS", "1") == "1"
WINDOW_NAME = os.getenv("WINDOW_NAME", "Face Recognition Attendance System")
MOBILE_CAM_URL = os.getenv("MOBILE_CAM_URL", "http://192.168.1.4:8080/video")


# -------------------------------------------------------------
# FACE RECOGNITION (ArcFace ONNX)
# -------------------------------------------------------------
FACE_RECOGNITION_MODEL = FR_DIR / "arc.onnx"


# -------------------------------------------------------------
# FACE LANDMARK DETECTOR (5-point ONNX)
# -------------------------------------------------------------
LANDMARK_MODEL = LM_DIR / "2dfan4.onnx"       # NEW