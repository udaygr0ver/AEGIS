import uuid
import datetime
import logging
import numpy as np
from sklearn.ensemble import IsolationForest
from sqlalchemy.orm import Session
from app.ml.feature_extractor import FeatureExtractor
from app.models import AlertItem

logger = logging.getLogger("siem.ml")

class AnomalyDetector:
    def __init__(self):
        self.model = IsolationForest(contamination=0.05, random_state=42)
        self.is_fitted = False

    def evaluate_and_alert(self, db: Session):
        extractor = FeatureExtractor(db)
        ip_list, X, log_ids_list = extractor.extract_ip_features(window_minutes=5)

        if len(ip_list) == 0 or X.shape[0] < 3:
            # Need minimum number of samples to evaluate anomaly scoring
            return

        try:
            # Fit model on current traffic window & predict anomaly labels (-1 = anomaly, 1 = normal)
            predictions = self.model.fit_predict(X)
            scores = self.model.decision_function(X) # lower score = more anomalous

            cutoff = datetime.datetime.utcnow() - datetime.timedelta(minutes=5)

            for idx, ip in enumerate(ip_list):
                if predictions[idx] == -1:
                    score = float(scores[idx])
                    
                    # Cooldown check for ML anomaly alerts
                    recent = db.query(AlertItem).filter(
                        AlertItem.rule_name == "ml_anomaly",
                        AlertItem.src_ip == ip,
                        AlertItem.triggered_at >= cutoff
                    ).first()

                    if recent:
                        continue

                    severity = "medium"
                    if score < -0.15:
                        severity = "critical"
                    elif score < -0.05:
                        severity = "high"

                    alert = AlertItem(
                        alert_uuid=str(uuid.uuid4()),
                        rule_name="ml_anomaly",
                        severity=severity,
                        title=f"Unsupervised ML Anomaly Detected on IP {ip}",
                        description=f"IsolationForest model flagged anomalous behavior pattern from IP {ip} (Anomaly Score: {score:.3f}).",
                        related_log_ids=log_ids_list[idx][:100],
                        src_ip=ip,
                        dest_ip="127.0.0.1",
                        triggered_at=datetime.datetime.utcnow(),
                        status="open"
                    )
                    db.add(alert)

            db.commit()
        except Exception as e:
            logger.error(f"Error during ML anomaly detection: {e}")

anomaly_detector = AnomalyDetector()
