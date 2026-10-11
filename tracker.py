import math
import time
from typing import Dict, List, Tuple
from config import TRACKER_MAX_DISAPPEARED, TRACKER_MAX_DISTANCE, COOLDOWN_SECONDS_BETWEEN_SAME_TRACK_LOG

class TrackedAnimal:
    def __init__(self, track_id: int, animal_name: str, bbox: List[int], confidence: float):
        self.track_id = track_id
        self.animal_name = animal_name
        self.bbox = bbox  # [x1, y1, x2, y2]
        self.confidence = confidence
        self.centroid = self._calculate_centroid(bbox)
        self.disappeared_count = 0
        self.first_seen = time.time()
        self.last_logged_time = 0.0
        self.logged_to_db = False

    def _calculate_centroid(self, bbox: List[int]) -> Tuple[int, int]:
        x1, y1, x2, y2 = bbox
        return int((x1 + x2) / 2), int((y1 + y2) / 2)

    def update(self, bbox: List[int], confidence: float):
        self.bbox = bbox
        self.confidence = confidence
        self.centroid = self._calculate_centroid(bbox)
        self.disappeared_count = 0

    def should_log_to_db(self) -> bool:
        """Determines if this detection should be written to database."""
        now = time.time()
        # Log first sighting immediately
        if not self.logged_to_db:
            self.logged_to_db = True
            self.last_logged_time = now
            return True

        # Heartbeat log if animal remains in frame for extended time
        if now - self.last_logged_time > COOLDOWN_SECONDS_BETWEEN_SAME_TRACK_LOG:
            self.last_logged_time = now
            return True

        return False


class AnimalTracker:
    """Lightweight Centroid & IoU Object Tracker for edge cameras."""

    def __init__(self, max_disappeared: int = TRACKER_MAX_DISAPPEARED, max_distance: int = TRACKER_MAX_DISTANCE):
        self.next_track_id = 1
        self.tracks: Dict[int, TrackedAnimal] = {}
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance

    def update(self, detections: List[Dict]) -> List[TrackedAnimal]:
        """
        detections: list of dicts with keys: 'name', 'confidence', 'bbox' ([x1, y1, x2, y2])
        Returns: list of active TrackedAnimal instances
        """
        if not detections:
            # Increment disappeared count for all active tracks
            disappeared_ids = []
            for track_id, track in self.tracks.items():
                track.disappeared_count += 1
                if track.disappeared_count > self.max_disappeared:
                    disappeared_ids.append(track_id)
            for track_id in disappeared_ids:
                del self.tracks[track_id]
            return list(self.tracks.values())

        if not self.tracks:
            # Register all current detections as new tracks
            for det in detections:
                track = TrackedAnimal(
                    track_id=self.next_track_id,
                    animal_name=det["name"],
                    bbox=det["bbox"],
                    confidence=det["confidence"]
                )
                self.tracks[self.next_track_id] = track
                self.next_track_id += 1
            return list(self.tracks.values())

        # Match existing tracks with current frame detections using Euclidean distance
        existing_ids = list(self.tracks.keys())
        existing_centroids = [self.tracks[tid].centroid for tid in existing_ids]

        matched_tracks = set()
        matched_detections = set()

        # Compute pairwise distances
        distance_matrix = []
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            det_centroid = (int((x1 + x2) / 2), int((y1 + y2) / 2))
            row = []
            for c in existing_centroids:
                dist = math.hypot(det_centroid[0] - c[0], det_centroid[1] - c[1])
                row.append(dist)
            distance_matrix.append(row)

        # Greedy match closest pairs
        for det_idx, det in enumerate(detections):
            min_dist = float('inf')
            best_track_idx = -1
            for track_idx, dist in enumerate(distance_matrix[det_idx]):
                if track_idx in matched_tracks:
                    continue
                # Also check same species label to avoid identity hopping
                if self.tracks[existing_ids[track_idx]].animal_name == det["name"] and dist < min_dist:
                    min_dist = dist
                    best_track_idx = track_idx

            if best_track_idx != -1 and min_dist <= self.max_distance:
                matched_tracks.add(best_track_idx)
                matched_detections.add(det_idx)
                track_id = existing_ids[best_track_idx]
                self.tracks[track_id].update(det["bbox"], det["confidence"])

        # Handle unmatched existing tracks
        for track_idx, track_id in enumerate(existing_ids):
            if track_idx not in matched_tracks:
                self.tracks[track_id].disappeared_count += 1

        # Purge dead tracks
        dead_tracks = [tid for tid, t in self.tracks.items() if t.disappeared_count > self.max_disappeared]
        for tid in dead_tracks:
            del self.tracks[tid]

        # Register unmatched new detections
        for det_idx, det in enumerate(detections):
            if det_idx not in matched_detections:
                track = TrackedAnimal(
                    track_id=self.next_track_id,
                    animal_name=det["name"],
                    bbox=det["bbox"],
                    confidence=det["confidence"]
                )
                self.tracks[self.next_track_id] = track
                self.next_track_id += 1

        return list(self.tracks.values())
