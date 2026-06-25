import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.database import get_db
from app.models import AlertItem, LogItem, User
from app.schemas import AlertResponse, AlertPaginatedResponse, AlertStatusUpdate, LogResponse
from app.auth import get_current_user

router = APIRouter(prefix="/alerts", tags=["Alerts & Triage"])

@router.get("", response_model=AlertPaginatedResponse)
def get_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    status: Optional[str] = None,
    severity: Optional[str] = None,
    rule_name: Optional[str] = None,
    src_ip: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(AlertItem)

    if status:
        query = query.filter(AlertItem.status == status)
    if severity:
        query = query.filter(AlertItem.severity == severity)
    if rule_name:
        query = query.filter(AlertItem.rule_name == rule_name)
    if src_ip:
        query = query.filter(AlertItem.src_ip == src_ip)

    total = query.count()
    items = query.order_by(desc(AlertItem.triggered_at)).offset((page - 1) * page_size).limit(page_size).all()

    return AlertPaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items
    )

@router.get("/trends")
def get_alert_trends(
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns alert counts bucketed for trends chart visualization."""
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(hours=hours)
    alerts = (
        db.query(AlertItem)
        .filter(AlertItem.triggered_at >= cutoff)
        .order_by(AlertItem.triggered_at.asc())
        .all()
    )

    # Group into hourly buckets
    buckets = {}
    for i in range(hours):
        t = (cutoff + datetime.timedelta(hours=i)).strftime("%Y-%m-%d %H:00")
        buckets[t] = {"time": t, "brute_force": 0, "port_scan": 0, "ddos_spike": 0, "privilege_escalation": 0, "ml_anomaly": 0, "total": 0}

    for a in alerts:
        bucket_key = a.triggered_at.strftime("%Y-%m-%d %H:00")
        if bucket_key in buckets:
            rule_key = a.rule_name if a.rule_name in buckets[bucket_key] else "brute_force"
            buckets[bucket_key][rule_key] += 1
            buckets[bucket_key]["total"] += 1

    return list(buckets.values())

@router.get("/{alert_id}")
def get_alert_detail(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    alert = db.query(AlertItem).filter(AlertItem.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Fetch related log items if present
    related_logs = []
    if alert.related_log_ids:
        related_logs = db.query(LogItem).filter(LogItem.id.in_(alert.related_log_ids)).all()

    return {
        "alert": AlertResponse.model_validate(alert),
        "related_logs": [LogResponse.model_validate(l) for l in related_logs]
    }

@router.patch("/{alert_id}/status", response_model=AlertResponse)
def update_alert_status(
    alert_id: int,
    payload: AlertStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if payload.status not in ("open", "acknowledged", "resolved"):
        raise HTTPException(status_code=400, detail="Invalid status value")

    alert = db.query(AlertItem).filter(AlertItem.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = payload.status
    db.commit()
    db.refresh(alert)
    return alert
