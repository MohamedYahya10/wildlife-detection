import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
SNAPSHOTS_DIR = DATA_DIR / "snapshots"
DB_PATH = DATA_DIR / "wildlife.db"
SAMPLES_DIR = BASE_DIR / "dataset" / "samples"
MODELS_DIR = BASE_DIR / "models"

# Ensure runtime directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# 10 Target Wildlife Species
SPECIES_LIST = [
    "Elephant",
    "Tiger",
    "Lion",
    "Leopard",
    "Bear",
    "Deer",
    "Giraffe",
    "Zebra",
    "Wolf",
    "Rhinoceros"
]

# Risk Classifications
RISK_LEVELS = {
    "Tiger": "CRITICAL",
    "Lion": "CRITICAL",
    "Leopard": "CRITICAL",
    "Elephant": "HIGH",
    "Bear": "HIGH",
    "Rhinoceros": "HIGH",
    "Wolf": "MEDIUM",
    "Deer": "LOW",
    "Giraffe": "LOW",
    "Zebra": "LOW"
}

# COCO to Wildlife Mapping (YOLO standard models)
COCO_WILDLIFE_MAPPING = {
    "elephant": "Elephant",
    "bear": "Bear",
    "zebra": "Zebra",
    "giraffe": "Giraffe",
    "horse": "Deer",      # Used as proxy when evaluating standard COCO
    "dog": "Wolf",        # Used as proxy when evaluating standard COCO
    "cat": "Leopard"      # Used as proxy when evaluating standard COCO
}

# Detection & Camera Defaults
DEFAULT_CONFIDENCE = 0.45
DEFAULT_IOU_THRESHOLD = 0.45
DEFAULT_CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# Tracker settings
TRACKER_MAX_DISAPPEARED = 30
TRACKER_MAX_DISTANCE = 80
COOLDOWN_SECONDS_BETWEEN_SAME_TRACK_LOG = 3.0
