from pathlib import Path
from typing import List, Dict, Any
import numpy as np
from ultralytics import YOLO


class FaceDetector:
    """
    YOLO-based face detector.
    Produces clean dictionary results:
        x1, y1, x2, y2, conf, cls_id, cls_name
    """

    def __init__(self, weights_path: Path, device="auto", conf=0.25, iou=0.45, img_size=640):
        self.model = YOLO(str(weights_path))

        self.kw = dict(
            conf=conf,
            iou=iou,
            imgsz=img_size,
            device=device,
            verbose=False
        )

        self.class_names = self.model.names

    def predict(self, frame_bgr: np.ndarray) -> List[Dict[str, Any]]:
        """
        Runs YOLO inference and returns bounding boxes in a normalized dict form.
        """
        results = self.model.predict(frame_bgr, **self.kw)

        detections: List[Dict[str, Any]] = []

        if not results:
            return detections

        r = results[0]

        if r.boxes is None or len(r.boxes) == 0:
            return detections

        boxes = r.boxes.xyxy.cpu().numpy()       # (N, 4)
        confs = r.boxes.conf.cpu().numpy()       # (N,)
        clss  = r.boxes.cls.cpu().numpy().astype(int)

        for (x1, y1, x2, y2), conf, cls_id in zip(boxes, confs, clss):
            detections.append({
                "x1": float(x1),
                "y1": float(y1),
                "x2": float(x2),
                "y2": float(y2),
                "conf": float(conf),
                "cls_id": int(cls_id),
                "cls_name": self.class_names.get(cls_id, str(cls_id)),
            })

        return detections