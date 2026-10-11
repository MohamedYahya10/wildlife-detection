import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from config import DB_PATH, RISK_LEVELS

class DatabaseManager:
    """Manages SQLite database connections, tables, and analytical queries."""

    def __init__(self, db_path=None):
        self.db_path = str(db_path or DB_PATH)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initializes tables and indexes for wildlife detection system."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Cameras table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cameras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    source_uri TEXT NOT NULL,
                    location TEXT NOT NULL,
                    status TEXT DEFAULT 'ACTIVE',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Detections table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    camera_id INTEGER DEFAULT 1,
                    animal_name TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    bounding_box TEXT,
                    track_id INTEGER DEFAULT -1,
                    risk_level TEXT NOT NULL,
                    snapshot_path TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (camera_id) REFERENCES cameras (id)
                );
            """)

            # Alerts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    detection_id INTEGER,
                    alert_type TEXT NOT NULL,
                    animal_name TEXT NOT NULL,
                    message TEXT NOT NULL,
                    resolved INTEGER DEFAULT 0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (detection_id) REFERENCES detections (id)
                );
            """)

            # Create performance indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_det_animal ON detections (animal_name);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_det_timestamp ON detections (timestamp);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_det_risk ON detections (risk_level);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_alert_resolved ON alerts (resolved);")

            # Insert default camera if not present
            cursor.execute("SELECT COUNT(*) FROM cameras;")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO cameras (name, source_uri, location, status)
                    VALUES ('North Perimeter AI Cam 1', '0', 'North Forest Gate - Sector 4', 'ACTIVE'),
                           ('Waterhole Safari Cam 2', 'sample.mp4', 'Main Waterhole - Sector 2', 'ACTIVE');
                """)
            conn.commit()

    def log_detection(self, animal_name: str, confidence: float, bbox: List[int],
                      track_id: int = -1, camera_id: int = 1,
                      snapshot_path: Optional[str] = None) -> int:
        """Logs an animal detection event and creates alert if high/critical risk."""
        risk = RISK_LEVELS.get(animal_name, "LOW")
        bbox_str = json.dumps(bbox) if bbox else "[]"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO detections (camera_id, animal_name, confidence, bounding_box, track_id, risk_level, snapshot_path, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
            """, (camera_id, animal_name, float(confidence), bbox_str, track_id, risk, snapshot_path))
            detection_id = cursor.lastrowid

            # Trigger automatic alert if dangerous wildlife
            if risk in ["CRITICAL", "HIGH"]:
                alert_type = f"{risk}_RISK_ALERT"
                msg = f"Alert! {animal_name} (Confidence: {confidence*100:.1f}%) detected on Camera {camera_id}."
                cursor.execute("""
                    INSERT INTO alerts (detection_id, alert_type, animal_name, message, resolved, timestamp)
                    VALUES (?, ?, ?, ?, 0, datetime('now', 'localtime'))
                """, (detection_id, alert_type, animal_name, msg))

            conn.commit()
            return detection_id

    def get_recent_detections(self, limit: int = 50, animal_filter: Optional[str] = None,
                             min_confidence: float = 0.0) -> List[Dict[str, Any]]:
        """Retrieves recent sightings with optional filters."""
        query = """
            SELECT d.id, d.camera_id, c.name as camera_name, d.animal_name,
                   d.confidence, d.bounding_box, d.track_id, d.risk_level,
                   d.snapshot_path, d.timestamp
            FROM detections d
            LEFT JOIN cameras c ON d.camera_id = c.id
            WHERE d.confidence >= ?
        """
        params = [min_confidence]
        if animal_filter and animal_filter != "All":
            query += " AND d.animal_name = ?"
            params.append(animal_filter)

        query += " ORDER BY d.id DESC LIMIT ?"
        params.append(limit)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_summary_statistics(self) -> Dict[str, Any]:
        """Calculates global analytics metrics."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM detections;")
            total_detections = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT animal_name) FROM detections;")
            unique_species = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM alerts WHERE resolved = 0;")
            active_alerts = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM cameras WHERE status = 'ACTIVE';")
            active_cameras = cursor.fetchone()[0]

            # Species breakdown
            cursor.execute("""
                SELECT animal_name, COUNT(*) as count, AVG(confidence) as avg_conf
                FROM detections
                GROUP BY animal_name
                ORDER BY count DESC
            """)
            species_counts = [dict(row) for row in cursor.fetchall()]

            # Risk breakdown
            cursor.execute("""
                SELECT risk_level, COUNT(*) as count
                FROM detections
                GROUP BY risk_level
            """)
            risk_counts = [dict(row) for row in cursor.fetchall()]

            # Hourly distribution
            cursor.execute("""
                SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
                FROM detections
                GROUP BY hour
                ORDER BY hour ASC
            """)
            hourly_counts = [dict(row) for row in cursor.fetchall()]

            return {
                "total_detections": total_detections,
                "unique_species": unique_species,
                "active_alerts": active_alerts,
                "active_cameras": active_cameras,
                "species_counts": species_counts,
                "risk_counts": risk_counts,
                "hourly_counts": hourly_counts
            }

    def get_recent_alerts(self, limit: int = 20, unresolved_only: bool = False) -> List[Dict[str, Any]]:
        """Fetches security and conservation alerts."""
        query = """
            SELECT a.id, a.detection_id, a.alert_type, a.animal_name, a.message,
                   a.resolved, a.timestamp, d.snapshot_path
            FROM alerts a
            LEFT JOIN detections d ON a.detection_id = d.id
        """
        params = []
        if unresolved_only:
            query += " WHERE a.resolved = 0"
        query += " ORDER BY a.id DESC LIMIT ?"
        params.append(limit)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def resolve_alert(self, alert_id: int):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE alerts SET resolved = 1 WHERE id = ?", (alert_id,))
            conn.commit()

# Global default instance
db = DatabaseManager()
