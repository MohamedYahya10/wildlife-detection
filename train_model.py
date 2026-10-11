import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def train_wildlife_yolo(
    epochs: int = 50,
    batch_size: int = 16,
    img_size: int = 640,
    model_variant: str = "yolov8n.pt"
):
    """Fine-tunes YOLO model on 10 Wildlife Animal Species dataset."""
    data_yaml = PROJECT_ROOT / "dataset" / "data.yaml"

    if not data_yaml.exists():
        print(f"[ERROR] Dataset configuration file not found at {data_yaml}")
        return

    print(f"[*] Starting YOLO Training for 10 Wildlife Animals...")
    print(f"    - Base Model: {model_variant}")
    print(f"    - Data YAML:  {data_yaml}")
    print(f"    - Epochs:     {epochs}")
    print(f"    - Batch Size: {batch_size}")
    print(f"    - Image Size: {img_size}")

    try:
        from ultralytics import YOLO

        model = YOLO(model_variant)
        results = model.train(
            data=str(data_yaml),
            epochs=epochs,
            batch=batch_size,
            imgsz=img_size,
            project=str(PROJECT_ROOT / "models"),
            name="wildlife_10_species",
            exist_ok=True,
            verbose=True
        )
        print("[SUCCESS] Model training complete! Saved to models/wildlife_10_species/weights/best.pt")
        return results
    except Exception as e:
        print(f"[TRAIN EXCEPTION] Error during training execution: {e}")

if __name__ == "__main__":
    train_wildlife_yolo(epochs=10, batch_size=8)
