import threading
import sys
import logging

try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("WildlifeAlert")

class AlertNotifier:
    """Dispatches audio, terminal, and system alerts when dangerous wildlife is detected."""

    def __init__(self, enable_sound: bool = True):
        self.enable_sound = enable_sound
        self._lock = threading.Lock()

    def _play_siren(self, frequency: int = 1200, duration_ms: int = 400):
        if not self.enable_sound:
            return
        if HAS_WINSOUND:
            try:
                winsound.Beep(frequency, duration_ms)
            except Exception:
                pass
        else:
            # Fallback bell
            sys.stdout.write('\a')
            sys.stdout.flush()

    def trigger_alert(self, animal_name: str, risk_level: str, camera_id: int = 1, confidence: float = 0.0):
        """Asynchronously triggers sound and notification based on risk."""
        logger.warning(
            f"🚨 WILDLIFE ALERT [{risk_level}] - {animal_name.upper()} "
            f"detected on Camera #{camera_id} with {confidence*100:.1f}% confidence!"
        )

        if risk_level == "CRITICAL":
            # Distinct double high-pitch pulse for apex predators
            threading.Thread(target=self._critical_siren_pattern, daemon=True).start()
        elif risk_level == "HIGH":
            # Single alert tone for elephants/bears/rhinos
            threading.Thread(target=lambda: self._play_siren(1000, 500), daemon=True).start()

    def _critical_siren_pattern(self):
        with self._lock:
            for _ in range(2):
                self._play_siren(1500, 250)
                self._play_siren(1100, 250)

# Global notifier
notifier = AlertNotifier(enable_sound=True)
