import time
import threading
import logging
from app.database import SessionLocal
from app.detection.rules import RuleEvaluator
from app.config import settings

logger = logging.getLogger("siem.detection")

class DetectionEngine:
    def __init__(self):
        self._running = False
        self._thread = None

    def _run_loop(self):
        logger.info("Detection Engine background loop started.")
        while self._running:
            db = SessionLocal()
            try:
                evaluator = RuleEvaluator(db)
                evaluator.evaluate_brute_force(window_minutes=5, threshold=5)
                evaluator.evaluate_port_scan(window_minutes=1, threshold=15)
                evaluator.evaluate_ddos(window_minutes=1, threshold=100)
                evaluator.evaluate_privilege_escalation(window_minutes=5)
            except Exception as e:
                logger.error(f"Error evaluating detection rules: {e}")
            finally:
                db.close()
            
            time.sleep(settings.DETECTION_INTERVAL_SECONDS)

    def start(self):
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()

    def stop(self):
        self._running = False

detection_engine = DetectionEngine()
