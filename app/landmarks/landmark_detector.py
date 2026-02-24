import onnxruntime as ort
import numpy as np
import cv2

from app.config.config import LANDMARK_MODEL


class LandmarkDetector:
    def __init__(self, model_path=str(LANDMARK_MODEL)):
        self.session = ort.InferenceSession(
            model_path,
            providers=['CPUExecutionProvider']
        )
        self.input_name = self.session.get_inputs()[0].name
        self.input_size = (640, 640)
        self.feat_strides = [8, 16, 32]
        self.num_anchors = 2
        self.conf_thresh = 0.04

    def _preprocess(self, img_bgr):
        img = cv2.resize(img_bgr, self.input_size)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(np.float32)
        img = (img - 127.5) / 128.0
        img = img.transpose(2, 0, 1)[np.newaxis, :]    # (1, 3, 640, 640)
        return img

    def _get_anchor_centers(self, stride, fh, fw):
        cx = np.arange(fw) * stride
        cy = np.arange(fh) * stride
        xv, yv = np.meshgrid(cx, cy)
        centers = np.stack([xv, yv], axis=-1).reshape(-1, 2).astype(np.float32)
        centers = np.repeat(centers, self.num_anchors, axis=0)
        return centers

    def _distance2kps(self, anchor_centers, kps_deltas):
        kps = np.zeros_like(kps_deltas)
        for i in range(0, kps_deltas.shape[1], 2):
            kps[:, i]     = anchor_centers[:, 0] + kps_deltas[:, i]
            kps[:, i + 1] = anchor_centers[:, 1] + kps_deltas[:, i + 1]
        return kps

    def predict(self, img_bgr: np.ndarray) -> np.ndarray | None:
        orig_h, orig_w = img_bgr.shape[:2]
        input_w, input_h = self.input_size

        scale_x = orig_w / input_w
        scale_y = orig_h / input_h

        blob = self._preprocess(img_bgr)
        outputs = self.session.run(None, {self.input_name: blob})

        # Outputs are grouped by type, then by stride (8, 16, 32)
        # scores: outputs[0,1,2]   shapes: (12800,1), (3200,1), (800,1)
        # bbox:   outputs[3,4,5]   shapes: (12800,4), (3200,4), (800,4)
        # kps:    outputs[6,7,8]   shapes: (12800,10),(3200,10),(800,10)

        best_score = -1
        best_kps = None

        for i, stride in enumerate(self.feat_strides):
            fh = input_h // stride
            fw = input_w // stride

            scores    = outputs[i].reshape(-1)          # (N,)
            kps_delta = outputs[i + 6].reshape(-1, 10)  # (N, 10)
            anchors   = self._get_anchor_centers(stride, fh, fw)  # (N, 2)

            mask = scores >= self.conf_thresh
            print(f"[DEBUG] Stride {stride}: max_score={scores.max():.4f}, anchors={len(scores)}")

            if not mask.any():
                continue

            scores_f    = scores[mask]
            kps_delta_f = kps_delta[mask]
            anchors_f   = anchors[mask]

            kps_decoded = self._distance2kps(anchors_f, kps_delta_f)

            best_idx = np.argmax(scores_f)
            if scores_f[best_idx] > best_score:
                best_score = scores_f[best_idx]
                best_kps   = kps_decoded[best_idx]

        if best_kps is None:
            return None

        kps = best_kps.reshape(5, 2)
        kps[:, 0] *= scale_x
        kps[:, 1] *= scale_y

        return kps