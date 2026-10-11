import cv2
import time
import numpy as np
from pathlib import Path
from typing import Optional, Tuple
from config import FRAME_WIDTH, FRAME_HEIGHT, SAMPLES_DIR

class CameraStream:
    """Manages video capture across Webcam, Video File, RTSP, and Synthetic Feeds."""

    def __init__(self, source: str = "0", width: int = FRAME_WIDTH, height: int = FRAME_HEIGHT):
        self.source = source
        self.width = width
        self.height = height
        self.cap = None
        self.is_synthetic = False
        self.synthetic_images = []
        self.synthetic_idx = 0
        self.last_synthetic_switch = 0
        self._initialize_source()

    def _initialize_source(self):
        """Opens video capture device or sets up fallback generator."""
        source_str = str(self.source).strip()

        # Check if integer webcam index
        if source_str.isdigit():
            cam_idx = int(source_str)
            print(f"[CameraStream] Connecting to hardware webcam index {cam_idx}...")
            self.cap = cv2.VideoCapture(cam_idx, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                print(f"[CameraStream] DirectShow failed; trying default capture for {cam_idx}...")
                self.cap = cv2.VideoCapture(cam_idx)
        else:
            # File or RTSP
            print(f"[CameraStream] Opening media stream/file: {source_str}...")
            self.cap = cv2.VideoCapture(source_str)

        # Check if capture opened successfully
        if self.cap is not None and self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            ret, test_frame = self.cap.read()
            if ret and test_frame is not None:
                self.is_synthetic = False
                print("[CameraStream] Camera stream successfully established.")
                return

        # If camera not available or opened, activate synthetic/sample stream
        print("[CameraStream] Hardware camera not available. Activating synthetic wildlife simulator stream.")
        self.is_synthetic = True
        self._load_synthetic_assets()

    def _load_synthetic_assets(self):
        """Loads sample wildlife imagery or generates demo test frames."""
        self.synthetic_images = []
        if SAMPLES_DIR.exists():
            for p in sorted(SAMPLES_DIR.glob("*.jpg")) + sorted(SAMPLES_DIR.glob("*.png")):
                img = cv2.imread(str(p))
                if img is not None:
                    self.synthetic_images.append(img)

        # If no sample files found yet, create baseline generated frames
        if not self.synthetic_images:
            for color, name in [
                ((30, 80, 40), "Savannah Habitat"),
                ((20, 50, 20), "Dense Jungle Corridor"),
                ((60, 60, 40), "Waterhole Sector")
            ]:
                blank = np.zeros((self.height, self.width, 3), dtype=np.uint8)
                blank[:] = color
                # Add grid / scenery lines
                cv2.rectangle(blank, (40, 40), (self.width - 40, self.height - 40), (100, 150, 100), 2)
                cv2.putText(blank, f"SIMULATED FEED: {name}", (60, 100),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                self.synthetic_images.append(blank)

    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Reads next frame from active source."""
        if not self.is_synthetic and self.cap is not None and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret and frame is not None:
                if frame.shape[1] != self.width or frame.shape[0] != self.height:
                    frame = cv2.resize(frame, (self.width, self.height))
                return True, frame
            else:
                # If looped video file reached EOF, rewind
                if not str(self.source).isdigit():
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = self.cap.read()
                    if ret and frame is not None:
                        return True, frame

        # Synthetic generator mode
        now = time.time()
        if now - self.last_synthetic_switch > 4.0:
            self.synthetic_idx = (self.synthetic_idx + 1) % len(self.synthetic_images)
            self.last_synthetic_switch = now

        frame = self.synthetic_images[self.synthetic_idx].copy()
        if frame.shape[1] != self.width or frame.shape[0] != self.height:
            frame = cv2.resize(frame, (self.width, self.height))

        # Add timestamp watermark
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, ts, (self.width - 220, self.height - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (220, 220, 220), 1)
        return True, frame

    def release(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
