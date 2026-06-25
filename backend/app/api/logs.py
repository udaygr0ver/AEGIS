import csv
import io
import uuid
import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, func

from app.database import get_db
from app.models import LogItem, User
from app.schemas import LogCreate, RawLogIngest, LogResponse, LogPaginatedResponse
from app.parsers.manager import parser_manager
from app.auth import get_current_user

router = APIRouter(prefix="/logs", tags=["Logs"])

@router.post("/ingest", response_model=LogResponse)
def ingest_log(payload: RawLogIngest, db: Session = Depends(get_db)):
    """Internal/Public endpoint for collectors to post raw log lines."""
    normalized = parser_manager.parse_log(
        raw_message=payload.raw_message,
        source_type=payload.source_type,
        source_host=payload.source_host or "localhost"
    )
    
    log_entry = LogItem(
        event_uuid=str(uuid.uuid4()),
        timestamp=normalized.timestamp or datetime.datetime.utcnow(),
        source_host=normalized.source_host,
        source_type=normalized.source_type,
        event_type=normalized.event_type,
        src_ip=normalized.src_ip,
        dest_ip=normalized.dest_ip,
        src_port=normalized.src_port,
        dest_port=normalized.dest_port,
        user=normalized.user,
        message_raw=normalized.message_raw,
        severity=normalized.severity,
        tags=normalized.tags
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry

@router.post("/ingest/batch")
def ingest_logs_batch(payloads: List[RawLogIngest], db: Session = Depends(get_db)):
    """Batch ingestion endpoint for high volume log lines."""
    log_objects = []
    for payload in payloads:
        normalized = parser_manager.parse_log(
            raw_message=payload.raw_message,
            source_type=payload.source_type,
            source_host=payload.source_host or "localhost"
        )
        log_objects.append(LogItem(
            event_uuid=str(uuid.uuid4()),
            timestamp=normalized.timestamp or datetime.datetime.utcnow(),
            source_host=normalized.source_host,
            source_type=normalized.source_type,
            event_type=normalized.event_type,
            src_ip=normalized.src_ip,
            dest_ip=normalized.dest_ip,
            src_port=normalized.src_port,
            dest_port=normalized.dest_port,
            user=normalized.user,
            message_raw=normalized.message_raw,
            severity=normalized.severity,
            tags=normalized.tags
        ))
    db.bulk_save_objects(log_objects)
    db.commit()
    return {"ingested_count": len(log_objects), "status": "success"}

@router.get("", response_model=LogPaginatedResponse)
def get_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    src_ip: Optional[str] = None,
    dest_ip: Optional[str] = None,
    source_type: Optional[str] = None,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    search: Optional[str] = None,
    start_time: Optional[datetime.datetime] = None,
    end_time: Optional[datetime.datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(LogItem)

    if src_ip:
        query = query.filter(LogItem.src_ip == src_ip)
    if dest_ip:
        query = query.filter(LogItem.dest_ip == dest_ip)
    if source_type:
        query = query.filter(LogItem.source_type == source_type)
    if event_type:
        query = query.filter(LogItem.event_type == event_type)
    if severity:
        query = query.filter(LogItem.severity == severity)
    if start_time:
        query = query.filter(LogItem.timestamp >= start_time)
    if end_time:
        query = query.filter(LogItem.timestamp <= end_time)
    if search:
        query = query.filter(
            or_(
                LogItem.message_raw.ilike(f"%{search}%"),
                LogItem.user.ilike(f"%{search}%"),
                LogItem.src_ip.ilike(f"%{search}%")
            )
        )

    total = query.count()
    items = query.order_by(desc(LogItem.timestamp)).offset((page - 1) * page_size).limit(page_size).all()

    return LogPaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items
    )

@router.get("/export.csv")
def export_logs_csv(
    src_ip: Optional[str] = None,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(1000, le=5000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(LogItem)
    if src_ip:
        query = query.filter(LogItem.src_ip == src_ip)
    if event_type:
        query = query.filter(LogItem.event_type == event_type)
    if severity:
        query = query.filter(LogItem.severity == severity)
    if search:
        query = query.filter(LogItem.message_raw.ilike(f"%{search}%"))

    logs = query.order_by(desc(LogItem.timestamp)).limit(limit).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "UUID", "Timestamp", "Source Host", "Source Type", "Event Type", "Src IP", "Dest IP", "Src Port", "Dest Port", "User", "Severity", "Raw Message"])
    
    for log in logs:
        writer.writerow([
            log.id, log.event_uuid, log.timestamp.isoformat(), log.source_host,
            log.source_type, log.event_type, log.src_ip or "", log.dest_ip or "",
            log.src_port or "", log.dest_port or "", log.user or "", log.severity,
            log.message_raw
        ])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=siem_logs_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"}
    )

@router.get("/{log_id}", response_model=LogResponse)
def get_log_by_id(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    log = db.query(LogItem).filter(LogItem.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log entry not found")
    return log
