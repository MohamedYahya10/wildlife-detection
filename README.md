# 🐾 10 Wildlife Animal Detection Using AI Camera

An intelligent computer vision surveillance, alerting, and ecological monitoring system built in Python. It detects, tracks, and logs **10 target wildlife species** in real-time using Deep Learning (**YOLOv8 / YOLOv11**), stores sighting records with image snapshots in a **SQLite** database, and provides an interactive **Streamlit** dashboard for monitoring and analytics.

---

## 🎯 10 Target Wildlife Species & Threat Classifications

| # | Species | Scientific Name | Threat / Risk Level | Conservation Status |
|---|---------|-----------------|---------------------|---------------------|
| 1 | **Elephant** | *Loxodonta africana* | **HIGH** | Endangered |
| 2 | **Tiger** | *Panthera tigris* | **CRITICAL** | Endangered |
| 3 | **Lion** | *Panthera leo* | **CRITICAL** | Vulnerable |
| 4 | **Leopard** | *Panthera pardus* | **CRITICAL** | Vulnerable |
| 5 | **Bear** | *Ursus arctos* | **HIGH** | Threatened |
| 6 | **Deer** | *Cervidae* | **LOW** | Least Concern |
| 7 | **Giraffe** | *Giraffa camelopardalis*| **LOW** | Vulnerable |
| 8 | **Zebra** | *Equus quagga* | **LOW** | Near Threatened |
| 9 | **Wolf** | *Canis lupus* | **MEDIUM** | Least Concern |
| 10 | **Rhinoceros** | *Rhinocerotidae* | **HIGH** | Critically Endangered |

---

## 📁 Project Structure

```
wildlife_detection/
├── app.py                     # Streamlit Interactive Monitoring Dashboard
├── main.py                    # Standalone CLI / Daemon Camera Runner
├── config.py                  # Global settings, class lists, and paths
├── requirements.txt           # Python package dependencies
├── README.md                  # Project documentation
│
├── database/
│   ├── __init__.py
│   └── db.py                  # SQLite schema, queries, metrics & alert logging
│
├── detector/
│   ├── __init__.py
│   ├── camera_stream.py       # Multi-source video streamer (Webcam, RTSP, Video, Synthetic)
│   ├── yolo_detector.py       # YOLO inference, class mapping, and visual HUD overlays
│   ├── tracker.py             # Centroid / IoU multi-object tracking (de-duplication)
│   └── species_meta.py        # Species ecological metadata and danger profiles
│
├── alert_system/
│   ├── __init__.py
│   └── notifier.py            # Audio siren patterns and alert dispatcher
│
├── data/
│   ├── wildlife.db            # SQLite database with sightings & alerts
│   └── snapshots/             # Cropped image evidence with bounding boxes
│
├── dataset/
│   ├── data.yaml              # YOLO dataset configuration
│   └── samples/               # Sample images and video assets
│
└── scripts/
    ├── download_samples.py    # Downloads/generates sample wildlife images
    ├── seed_database.py       # Seeds historical sightings for analytics
    └── train_model.py         # YOLO fine-tuning pipeline script
```

---

## 🚀 Quick Start Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Download Sample Wildlife Data & Seed Database
Prepare the system with sample imagery and historical sightings:
```bash
# Download sample images for all 10 animals
python scripts/download_samples.py

# Seed SQLite database with realistic historical sightings & alerts
python scripts/seed_database.py
```

### 3. Launch the Interactive Web Dashboard
Run the Streamlit monitoring center:
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### 4. Run Standalone CLI AI Camera Detection
To run continuous camera surveillance directly in terminal or as a service:
```bash
# Monitor default webcam (index 0)
python main.py --source 0 --conf 0.45

# Monitor a video file or test simulation
python main.py --source dataset/samples/sample.mp4

# Run headless (no preview window) for edge servers / Raspberry Pi / Jetson
python main.py --source 0 --no-window --conf 0.50
```

---

## 📊 Database Schema Details (SQLite)

The system automatically manages `data/wildlife.db` with the following indexed tables:

1. **`cameras`**: Stores camera hardware metadata, RTSP addresses, and geographic sectors.
2. **`detections`**: Records every sighting with:
   - `animal_name`: Target species detected.
   - `confidence`: AI detection probability (0.0 to 1.0).
   - `bounding_box`: Pixel coordinates `[x1, y1, x2, y2]`.
   - `track_id`: Unique tracking ID across video frames.
   - `risk_level`: `CRITICAL`, `HIGH`, `MEDIUM`, or `LOW`.
   - `snapshot_path`: Relative link to photographic evidence.
   - `timestamp`: Date and time of sighting.
3. **`alerts`**: High/Critical risk triggers requiring forest ranger intervention, with resolution status tracking.

---

## 🧠 Fine-Tuning YOLO on Custom Wildlife Datasets

To train a custom YOLO model on your own dataset:
1. Organize your annotated images in `dataset/images/train`, `dataset/images/val` and labels in `dataset/labels/train`, `dataset/labels/val`.
2. Run the training script:
```bash
python scripts/train_model.py
```
Weights will be saved to `models/wildlife_10_species/weights/best.pt`.
