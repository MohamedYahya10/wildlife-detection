import cv2
import time
import argparse
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import (
    DEFAULT_CAMERA_INDEX,
    DEFAULT_CONFIDENCE,
    SNAPSHOTS_DIR,
    RISK_LEVELS
)
from detector.camera_stream import CameraStream
from detector.yolo_detector import YOLOWildlifeDetector
from detector.tracker import AnimalTracker
from database.db import db
from alert_system.notifier import notifier

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def run_camera_detection(
    source="0",
    conf_threshold=DEFAULT_CONFIDENCE,
    camera_id=1,
    show_window=True,
    enable_sound=True,
    model_name="yolov8n.pt",
    max_frames=None
):
    print("=" * 65)
    print(" [AI CAMERA] 10 WILDLIFE ANIMAL DETECTION & SURVEILLANCE")
    print("=" * 65)
    print(f"[*] Source:           {source}")
    print(f"[*] Camera ID:        {camera_id}")
    print(f"[*] Model:            {model_name}")
    print(f"[*] Confidence:       {conf_threshold * 100:.0f}%")
    print(f"[*] Display Window:   {show_window}")
    print(f"[*] Sound Alerts:     {enable_sound}")
    print("=" * 65)

    # Initialize modules
    notifier.enable_sound = enable_sound
    stream = CameraStream(source=source)
    detector = YOLOWildlifeDetector(model_name=model_name, conf_thresh=conf_threshold)
    tracker = AnimalTracker()

    fps_start_time = time.time()
    frame_count = 0
    fps = 0.0

    print("\n[AI CAMERA] Monitoring active. Press 'q' in the video window or Ctrl+C in terminal to exit.\n")

    try:
        while True:
            ret, frame = stream.read_frame()
            if not ret or frame is None:
                print("[AI CAMERA] Stream ended or unavailable.")
                break

            frame_count += 1
            if max_frames and frame_count >= max_frames:
                print(f"[AI CAMERA] Reached target frame limit of {max_frames}. Exiting.")
                break

            if frame_count % 15 == 0:
                now = time.time()
                elapsed = now - fps_start_time
                if elapsed > 0:
                    fps = 15 / elapsed
                fps_start_time = now

            # Step 1: Detect wildlife in current frame
            raw_detections = detector.detect(frame, conf_threshold=conf_threshold)

            # Step 2: Track across frames (deduplication)
            tracked_animals = tracker.update(raw_detections)

            # Step 3: Process detections and log to SQLite database
            for track in tracked_animals:
                if track.should_log_to_db():
                    animal_name = track.animal_name
                    conf = track.confidence
                    risk = RISK_LEVELS.get(animal_name, "LOW")

                    # Save snapshot evidence
                    ts_filename = time.strftime("%Y%m%d_%H%M%S")
                    snapshot_filename = f"{animal_name.lower()}_track{track.track_id}_{ts_filename}.jpg"
                    full_snapshot_path = SNAPSHOTS_DIR / snapshot_filename

                    # Save cropped animal image with padding
                    x1, y1, x2, y2 = track.bbox
                    h, w = frame.shape[:2]
                    crop_x1 = max(0, x1 - 15)
                    crop_y1 = max(0, y1 - 15)
                    crop_x2 = min(w, x2 + 15)
                    crop_y2 = min(h, y2 + 15)
                    crop = frame[crop_y1:crop_y2, crop_x1:crop_x2]
                    if crop.size > 0:
                        cv2.imwrite(str(full_snapshot_path), crop)
                        rel_path = f"snapshots/{snapshot_filename}"
                    else:
                        rel_path = None

                    # Log to database
                    det_id = db.log_detection(
                        animal_name=animal_name,
                        confidence=conf,
                        bbox=track.bbox,
                        track_id=track.track_id,
                        camera_id=camera_id,
                        snapshot_path=rel_path
                    )

                    print(f"[*] [DB LOG #{det_id}] Sighted: {animal_name} ({conf*100:.1f}%) | Track #{track.track_id} | Risk: {risk}")

                    # Trigger alert if high risk
                    if risk in ["CRITICAL", "HIGH"]:
                        notifier.trigger_alert(animal_name, risk, camera_id=camera_id, confidence=conf)

            # Step 4: Render annotations
            annotated_frame = detector.draw_overlays(frame, tracked_animals)

            # Render FPS & status
            cv2.putText(
                annotated_frame,
                f"FPS: {fps:.1f} | Active Tracks: {len(tracked_animals)}",
                (annotated_frame.shape[1] - 220, 24),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 255, 0),
                1,
                cv2.LINE_AA
            )

            # Step 5: Optional preview window
            if show_window:
                cv2.imshow("10 Wildlife Animal Detection - AI Camera Feed", annotated_frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("[AI CAMERA] User pressed 'q'. Shutting down surveillance.")
                    break

    except KeyboardInterrupt:
        print("\n[AI CAMERA] Surveillance stopped by user.")
    finally:
        stream.release()
        if show_window:
            cv2.destroyAllWindows()
        print("[AI CAMERA] Resources successfully cleaned up.")

def main():
    parser = argparse.ArgumentParser(description="10 Wildlife Animal Detection Using AI Camera")
    parser.add_argument("--source", type=str, default="0", help="Camera index (e.g. 0), video file path, or RTSP URL")
    parser.add_argument("--conf", type=float, default=DEFAULT_CONFIDENCE, help="Detection confidence threshold (0.1 - 1.0)")
    parser.add_argument("--camera-id", type=int, default=1, help="Camera ID in database")
    parser.add_argument("--model", type=str, default="yolov8n.pt", help="YOLO model path or name")
    parser.add_argument("--frames", type=int, default=None, help="Maximum number of frames to process before exiting")
    parser.add_argument("--no-window", action="store_true", help="Run in headless background mode without GUI window")
    parser.add_argument("--mute", action="store_true", help="Disable audio siren alerts")

    args = parser.parse_args()

    run_camera_detection(
        source=args.source,
        conf_threshold=args.conf,
        camera_id=args.camera_id,
        show_window=not args.no_window,
        enable_sound=not args.mute,
        model_name=args.model,
        max_frames=args.frames
    )

if __name__ == "__main__":
    main()
