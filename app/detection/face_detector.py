from pathlib import Path
from typing import List, Dict, Any
import numpy as np

from ultralytics import YOLO

class FaceDetector:
    """Thin wrapper for Ultralytics YOLO models."""
    def __init__(self, weights_path: Path, device="auto", conf=0.25, iou=0.45, img_size=640):
        self.model = YOLO(str(weights_path))
        self.kw = dict(conf=conf, iou=iou, imgsz=img_size, device=device, verbose=False)
        self.class_names = self.model.names  # e.g. {0: 'face'}

    def predict(self, frame_bgr: np.ndarray) -> List[Dict[str, Any]]:
        results = self.model.predict(frame_bgr, **self.kw)
        dets: List[Dict[str, Any]] = []
        if not results:
            return dets
        r = results[0]
        if r.boxes is None or len(r.boxes) == 0:
            return dets
        boxes = r.boxes.xyxy.cpu().numpy()
        confs = r.boxes.conf.cpu().numpy()
        clss  = r.boxes.cls.cpu().numpy().astype(int)
        for (x1, y1, x2, y2), c, k in zip(boxes, confs, clss):
            dets.append({
                "x1": float(x1), "y1": float(y1), "x2": float(x2), "y2": float(y2),
                "conf": float(c), "cls_id": int(k), "cls_name": self.model.names.get(int(k), str(k)),
            })
        return dets
