import cv2
import numpy as np
from typing import List, Dict, Any, Tuple
from config import (
    SPECIES_LIST,
    COCO_WILDLIFE_MAPPING,
    DEFAULT_CONFIDENCE,
    DEFAULT_IOU_THRESHOLD,
    RISK_LEVELS,
    MODELS_DIR
)
from detector.species_meta import get_species_info

class YOLOWildlifeDetector:
    """YOLO-based Animal Detection Engine for 10 Target Wildlife Species."""

    def __init__(self, model_name: str = "wildlife_10_species/weights/best.pt", conf_thresh: float = DEFAULT_CONFIDENCE):
        self.model_name = model_name
        self.conf_thresh = conf_thresh
        self.model = None
        self.is_custom_model = False
        self._load_model()

    def _load_model(self):
        """Loads Ultralytics YOLO model or falls back gracefully."""
        try:
            from ultralytics import YOLO
            # Check if custom fine-tuned weights exist in models/
            custom_path = MODELS_DIR / self.model_name
            if custom_path.exists():
                print(f"[YOLO] Loading custom fine-tuned weights from {custom_path}")
                self.model = YOLO(str(custom_path))
                self.is_custom_model = True
            else:
                print(f"[YOLO] Loading standard YOLO weights: {self.model_name}")
                self.model = YOLO(self.model_name)
                self.is_custom_model = False
            print("[YOLO] AI Vision Engine initialized successfully.")
        except Exception as e:
            print(f"[YOLO WARNING] Could not initialize Ultralytics: {e}. Running in simulation/heuristic mode.")
            self.model = None

    def detect(self, frame: np.ndarray, conf_threshold: float = None) -> List[Dict[str, Any]]:
        """
        Runs inference on an OpenCV BGR frame.
        Returns: list of detections with format:
          [{ 'name': 'Elephant', 'confidence': 0.88, 'bbox': [x1, y1, x2, y2], 'risk': 'HIGH' }]
        """
        threshold = conf_threshold if conf_threshold is not None else self.conf_thresh
        detections = []

        if frame is None or frame.size == 0:
            return detections

        if self.model is not None:
            try:
                results = self.model.predict(
                    source=frame,
                    conf=threshold,
                    iou=DEFAULT_IOU_THRESHOLD,
                    verbose=False
                )

                for r in results:
                    boxes = r.boxes
                    for box in boxes:
                        cls_id = int(box.cls[0].item())
                        conf = float(box.conf[0].item())
                        cls_name = r.names[cls_id].lower()

                        mapped_name = None
                        if self.is_custom_model:
                            # Direct 10 classes
                            mapped_name = r.names[cls_id]
                        else:
                            # Map standard COCO classes
                            if cls_name in COCO_WILDLIFE_MAPPING:
                                mapped_name = COCO_WILDLIFE_MAPPING[cls_name]
                            elif cls_name in [s.lower() for s in SPECIES_LIST]:
                                # Exact match
                                for s in SPECIES_LIST:
                                    if s.lower() == cls_name:
                                        mapped_name = s
                                        break

                        if mapped_name and mapped_name in SPECIES_LIST:
                            xyxy = box.xyxy[0].cpu().numpy().astype(int).tolist()
                            detections.append({
                                "name": mapped_name,
                                "confidence": round(conf, 3),
                                "bbox": xyxy,
                                "risk": RISK_LEVELS.get(mapped_name, "LOW")
                            })
                return detections
            except Exception as e:
                print(f"[YOLO Inference Error] {e}")

        return detections

    def draw_overlays(self, frame: np.ndarray, tracked_animals: List[Any]) -> np.ndarray:
        """Draws visual bounding boxes, risk badges, track IDs, and confidence on frame."""
        annotated = frame.copy()
        h, w = annotated.shape[:2]

        # Draw heads-up display header
        cv2.rectangle(annotated, (0, 0), (w, 35), (20, 20, 20), -1)
        cv2.putText(
            annotated,
            "AI WILDLIFE CAMERA - 10 SPECIES MONITOR",
            (15, 24),
            cv2.FONT_HERSHEY_DUPLEX,
            0.65,
            (240, 240, 240),
            1,
            cv2.LINE_AA
        )

        for track in tracked_animals:
            x1, y1, x2, y2 = track.bbox
            name = track.animal_name
            conf = track.confidence
            track_id = track.track_id
            risk = RISK_LEVELS.get(name, "LOW")

            # Color scheme by risk level (BGR)
            if risk == "CRITICAL":
                box_color = (40, 40, 230)      # Bright Red
            elif risk == "HIGH":
                box_color = (0, 140, 255)      # Orange
            elif risk == "MEDIUM":
                box_color = (0, 215, 255)      # Yellow/Gold
            else:
                box_color = (80, 210, 80)      # Green

            # Bounding box with rounded look or corner accents
            cv2.rectangle(annotated, (x1, y1), (x2, y2), box_color, 2)

            # Corner brackets for tactical look
            corner_len = min(20, (x2 - x1) // 4, (y2 - y1) // 4)
            # Top-left
            cv2.line(annotated, (x1, y1), (x1 + corner_len, y1), box_color, 4)
            cv2.line(annotated, (x1, y1), (x1, y1 + corner_len), box_color, 4)
            # Top-right
            cv2.line(annotated, (x2, y1), (x2 - corner_len, y1), box_color, 4)
            cv2.line(annotated, (x2, y1), (x2, y1 + corner_len), box_color, 4)
            # Bottom-left
            cv2.line(annotated, (x1, y2), (x1 + corner_len, y2), box_color, 4)
            cv2.line(annotated, (x1, y2), (x1, y2 - corner_len), box_color, 4)
            # Bottom-right
            cv2.line(annotated, (x2, y2), (x2 - corner_len, y2), box_color, 4)
            cv2.line(annotated, (x2, y2), (x2, y2 - corner_len), box_color, 4)

            # Label banner
            label = f"ID#{track_id} {name} {int(conf * 100)}% [{risk}]"
            (text_w, text_h), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.52, 1)

            banner_y1 = max(0, y1 - text_h - 10)
            banner_y2 = y1
            cv2.rectangle(annotated, (x1, banner_y1), (x1 + text_w + 10, banner_y2), box_color, -1)
            cv2.putText(
                annotated,
                label,
                (x1 + 5, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.52,
                (255, 255, 255),
                1,
                cv2.LINE_AA
            )

        return annotated
