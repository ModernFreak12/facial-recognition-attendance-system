import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT / "models"
FD_DIR = MODELS_DIR / "face_detection_new"

def _latest(paths):
    paths = [p for p in paths if p.exists()]
    return max(paths, key=lambda p: p.stat().st_mtime) if paths else None

def _auto_weights() -> Path:
    # 1) best*.pt under models/face_detection/runs/**/weights/
    best = _latest(FD_DIR.glob("runs/**/weights/best*.pt"))
    if best:
        return best

    # 2) any .pt directly under models/face_detection (newest first)
    any_fd = _latest(FD_DIR.glob("*.pt"))
    if any_fd:
        return any_fd

    # 3) any .pt under top-level models/
    any_models = _latest(MODELS_DIR.glob("*.pt"))
    if any_models:
        return any_models

    raise FileNotFoundError("No .pt weights found under models/face_detection or models/")

# Allow override via env var
WEIGHTS_PATH = Path(os.getenv("WEIGHTS_PATH", _auto_weights()))

# Inference knobs
CONF     = float(os.getenv("CONF", "0.7"))
IOU      = float(os.getenv("IOU", "0.5"))
IMG_SIZE = 2208
DEVICE   = "cpu"

# Video / UI
CAM_INDEX   = int(os.getenv("CAM_INDEX", "0"))
SHOW_FPS    = os.getenv("SHOW_FPS", "1") == "1"
WINDOW_NAME = os.getenv("WINDOW_NAME", "Face Detect")
