from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.database import get_db
from app.models import LogItem, AlertItem, User
from app.schemas import DashboardStats, SeverityCounts, TopAttacker
from app.auth import get_current_user

router = APIRouter(prefix="/stats", tags=["Statistics & Analytics"])

@router.get("/overview", response_model=DashboardStats)
def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    total_logs = db.query(func.count(LogItem.id)).scalar() or 0
    total_alerts = db.query(func.count(AlertItem.id)).scalar() or 0
    open_alerts = db.query(func.count(AlertItem.id)).filter(AlertItem.status == 'open').scalar() or 0
    critical_alerts = db.query(func.count(AlertItem.id)).filter(AlertItem.severity == 'critical', AlertItem.status == 'open').scalar() or 0

    # Log severity counts
    log_sev_rows = db.query(LogItem.severity, func.count(LogItem.id)).group_by(LogItem.severity).all()
    log_sev_dict = {sev: count for sev, count in log_sev_rows}
    logs_severity = SeverityCounts(
        low=log_sev_dict.get('low', 0),
        medium=log_sev_dict.get('medium', 0),
        high=log_sev_dict.get('high', 0),
        critical=log_sev_dict.get('critical', 0)
    )

    # Alert severity counts
    alert_sev_rows = db.query(AlertItem.severity, func.count(AlertItem.id)).group_by(AlertItem.severity).all()
    alert_sev_dict = {sev: count for sev, count in alert_sev_rows}
    alerts_severity = SeverityCounts(
        low=alert_sev_dict.get('low', 0),
        medium=alert_sev_dict.get('medium', 0),
        high=alert_sev_dict.get('high', 0),
        critical=alert_sev_dict.get('critical', 0)
    )

    # Top Attackers (Grouped by src_ip in alerts)
    attacker_rows = (
        db.query(
            AlertItem.src_ip,
            func.count(AlertItem.id).label('alert_count')
        )
        .filter(AlertItem.src_ip.isnot(None), AlertItem.src_ip != '127.0.0.1')
        .group_by(AlertItem.src_ip)
        .order_by(desc('alert_count'))
        .limit(5)
        .all()
    )

    top_attackers = []
    for row in attacker_rows:
        ip = row[0]
        a_count = row[1]
        log_cnt = db.query(func.count(LogItem.id)).filter(LogItem.src_ip == ip).scalar() or 0
        
        # Determine highest severity for this attacker
        highest_sev = db.query(AlertItem.severity).filter(AlertItem.src_ip == ip).order_by(desc(AlertItem.id)).first()
        sev_str = highest_sev[0] if highest_sev else "high"

        top_attackers.append(TopAttacker(
            src_ip=ip,
            alert_count=a_count,
            log_count=log_cnt,
            highest_severity=sev_str
        ))

    return DashboardStats(
        total_logs=total_logs,
        total_alerts=total_alerts,
        open_alerts=open_alerts,
        critical_alerts=critical_alerts,
        logs_by_severity=logs_severity,
        alerts_by_severity=alerts_severity,
        top_attackers=top_attackers
    )
