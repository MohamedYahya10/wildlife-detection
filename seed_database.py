import sys
import random
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.db import db
from config import SPECIES_LIST, RISK_LEVELS

def seed_sample_sightings(num_records: int = 120):
    """Populates the SQLite database with diverse historical wildlife sightings."""
    print(f"[*] Seeding SQLite database with {num_records} realistic sightings across 10 species...")

    now = datetime.now()
    cameras = [1, 2] # 1: North Perimeter, 2: Waterhole Safari Cam

    # Weighted species occurrence to reflect realistic ecology
    species_weights = {
        "Deer": 30,
        "Zebra": 22,
        "Giraffe": 18,
        "Elephant": 15,
        "Wolf": 10,
        "Bear": 8,
        "Leopard": 6,
        "Rhinoceros": 5,
        "Lion": 4,
        "Tiger": 2
    }

    weighted_pool = []
    for sp, weight in species_weights.items():
        weighted_pool.extend([sp] * weight)

    with db.get_connection() as conn:
        cursor = conn.cursor()

        # Check if already seeded
        cursor.execute("SELECT COUNT(*) FROM detections;")
        current_count = cursor.fetchone()[0]
        if current_count >= num_records:
            print(f"[!] Database already contains {current_count} detection records. Skipping seed.")
            return

        for i in range(num_records):
            animal = random.choice(weighted_pool)
            cam = random.choice(cameras)
            conf = round(random.uniform(0.68, 0.98), 2)
            risk = RISK_LEVELS.get(animal, "LOW")

            # Simulate timestamp within the last 7 days
            days_ago = random.uniform(0, 7)
            # Predators more likely at dawn/dusk/night
            if risk in ["CRITICAL", "HIGH"] and random.random() < 0.7:
                hour = random.choice([20, 21, 22, 23, 0, 1, 2, 3, 4, 5])
            else:
                hour = random.randint(6, 19)

            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            ts = (now - timedelta(days=days_ago)).replace(hour=hour, minute=minute, second=second)
            ts_str = ts.strftime("%Y-%m-%d %H:%M:%S")

            # Bounding box mock
            x1 = random.randint(30, 200)
            y1 = random.randint(50, 180)
            x2 = x1 + random.randint(120, 300)
            y2 = y1 + random.randint(100, 240)
            bbox_str = f"[{x1}, {y1}, {x2}, {y2}]"
            track_id = random.randint(100, 999)
            snapshot_path = f"snapshots/{animal.lower()}_sample.jpg"

            cursor.execute("""
                INSERT INTO detections (camera_id, animal_name, confidence, bounding_box, track_id, risk_level, snapshot_path, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (cam, animal, conf, bbox_str, track_id, risk, snapshot_path, ts_str))
            det_id = cursor.lastrowid

            # Create Alert for high / critical risk
            if risk in ["CRITICAL", "HIGH"]:
                resolved = 1 if days_ago > 1.5 else random.choice([0, 1])
                msg = f"Alert! {animal} ({int(conf*100)}% conf) spotted at Camera #{cam} ({'North Perimeter' if cam==1 else 'Waterhole'})."
                cursor.execute("""
                    INSERT INTO alerts (detection_id, alert_type, animal_name, message, resolved, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (det_id, f"{risk}_RISK_ALERT", animal, msg, resolved, ts_str))

        conn.commit()

    print("[SUCCESS] Database seeded successfully!")

if __name__ == "__main__":
    seed_sample_sightings()
