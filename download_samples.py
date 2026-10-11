import os
import sys
import urllib.request
import cv2
import numpy as np
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import SAMPLES_DIR, SNAPSHOTS_DIR, SPECIES_LIST
from detector.species_meta import get_species_info

# Wikimedia / Public domain verified URLs for high quality wildlife samples
SAMPLE_URLS = {
    "Elephant": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/37/African_Bush_Elephant.jpg/640px-African_Bush_Elephant.jpg",
    "Tiger": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Tiger.50.jpg/640px-Tiger.50.jpg",
    "Lion": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/73/Lion_waiting_in_Namibia.jpg/640px-Lion_waiting_in_Namibia.jpg",
    "Leopard": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/06/Amur_Leopard_7.jpg/640px-Amur_Leopard_7.jpg",
    "Bear": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/71/2010-kodiak-bear-1.jpg/640px-2010-kodiak-bear-1.jpg",
    "Deer": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b7/White-tailed_deer.jpg/640px-White-tailed_deer.jpg",
    "Giraffe": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/Giraffe_Mikumi_National_Park.jpg/640px-Giraffe_Mikumi_National_Park.jpg",
    "Zebra": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e3/Plains_Zebra_Equus_quagga.jpg/640px-Plains_Zebra_Equus_quagga.jpg",
    "Wolf": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/68/Eurasian_wolf_2.jpg/640px-Eurasian_wolf_2.jpg",
    "Rhinoceros": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/16/Ceratotherium_simum_krokodill.jpg/640px-Ceratotherium_simum_krokodill.jpg"
}

def generate_fallback_image(animal_name: str, file_path: Path):
    """Generates an informative simulated wildlife test image if internet is offline."""
    info = get_species_info(animal_name)
    img = np.zeros((480, 640, 3), dtype=np.uint8)

    # Scenery background gradient
    for y in range(480):
        factor = y / 480.0
        # Savannah / Forest green-brown gradient
        r = int(35 * (1 - factor) + 60 * factor)
        g = int(60 * (1 - factor) + 90 * factor)
        b = int(25 * (1 - factor) + 40 * factor)
        img[y, :] = (b, g, r)

    # Habitat overlay
    cv2.rectangle(img, (50, 50), (590, 430), (100, 180, 100), 2)

    # Animal Badge Box
    cv2.rectangle(img, (140, 120), (500, 340), (20, 20, 20), -1)
    cv2.rectangle(img, (140, 120), (500, 340), (0, 215, 255), 2)

    # Animal Text
    cv2.putText(img, f"{info['icon']} {animal_name.upper()}", (160, 180),
                cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255), 2)
    cv2.putText(img, f"Scientific: {info['scientific_name']}", (160, 220),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
    cv2.putText(img, f"Threat Level: {info['risk_level']}", (160, 255),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 120, 255), 2)
    cv2.putText(img, f"Status: {info['conservation_status']}", (160, 285),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)
    cv2.putText(img, "WILDLIFE CAMERA SIMULATION FEED", (150, 415),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 255, 150), 1)

    cv2.imwrite(str(file_path), img)

def download_or_generate_samples():
    print("[*] Preparing Wildlife Dataset Samples for 10 Species...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    for animal, url in SAMPLE_URLS.items():
        sample_path = SAMPLES_DIR / f"{animal.lower()}.jpg"
        snapshot_path = SNAPSHOTS_DIR / f"{animal.lower()}_sample.jpg"

        if not sample_path.exists():
            print(f" -> Fetching {animal} sample image...")
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = response.read()
                    with open(sample_path, "wb") as f:
                        f.write(data)
                    # Also copy to snapshot gallery for quick preview
                    with open(snapshot_path, "wb") as f:
                        f.write(data)
                print(f"    [OK] Downloaded {animal}")
            except Exception as e:
                print(f"    [Fallback] Network timeout or blocked ({e}). Generating synthetic asset for {animal}...")
                generate_fallback_image(animal, sample_path)
                generate_fallback_image(animal, snapshot_path)
        else:
            print(f"    [Existing] {animal} sample already present.")

    print("\n[SUCCESS] All 10 wildlife species sample assets are ready in:")
    print(f" - {SAMPLES_DIR}")
    print(f" - {SNAPSHOTS_DIR}")

if __name__ == "__main__":
    download_or_generate_samples()
