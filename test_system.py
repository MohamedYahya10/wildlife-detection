import sys
import time
import numpy as np
from pathlib import Path

# Add project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from detector.yolo_detector import YOLOWildlifeDetector
from detector.tracker import AnimalTracker
from detector.camera_stream import CameraStream
from database.db import db
from config import SAMPLES_DIR

def run_smoke_tests():
    print("=" * 60)
    print("RUNNING WILDLIFE SYSTEM SMOKE TESTS")
    print("=" * 60)

    # 1. Database Test
    print("[1/4] Checking SQLite Database...")
    stats = db.get_summary_statistics()
    print(f"      Total Sightings: {stats['total_detections']}")
    print(f"      Species Found:   {stats['unique_species']} / 10")
    print("      [PASS] Database functional.")

    # 2. Camera Stream Test
    print("\n[2/4] Testing CameraStream...")
    cam = CameraStream(source="sample.mp4")
    ret, frame = cam.read_frame()
    assert ret and frame is not None, "Failed to read frame from CameraStream"
    print(f"      Frame acquired: shape={frame.shape}")
    cam.release()
    print("      [PASS] CameraStream functional.")

    # 3. YOLO Model Test
    print("\n[3/4] Initializing YOLO Detector...")
    detector = YOLOWildlifeDetector(model_name="yolov8n.pt", conf_thresh=0.25)
    print("      Testing inference on test frame...")
    dets = detector.detect(frame)
    print(f"      Inference output count: {len(dets)}")
    print("      [PASS] YOLO detector functional.")

    # 4. Multi-Animal Tracker Test
    print("\n[4/4] Testing Animal Tracker...")
    tracker = AnimalTracker()
    dummy_dets = [
        {"name": "Elephant", "confidence": 0.92, "bbox": [100, 100, 250, 300]},
        {"name": "Tiger", "confidence": 0.88, "bbox": [320, 150, 480, 290]}
    ]
    tracks = tracker.update(dummy_dets)
    assert len(tracks) == 2, "Expected 2 tracked animals"
    print(f"      Tracked objects: {[t.animal_name for t in tracks]}")
    print("      [PASS] Tracker functional.")

    print("\n" + "=" * 60)
    print("ALL 4 SMOKE TESTS PASSED SUCCESSFULLY! 🚀")
    print("=" * 60)

if __name__ == "__main__":
    run_smoke_tests()
