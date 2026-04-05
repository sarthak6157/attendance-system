"""Attendance routes."""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DBSession

from core.security import get_current_user, require_roles
from db.database import get_db
from models.models import AttendanceMethod, AttendanceRecord, AttendanceStatus, Session, SessionStatus, User, UserRole
from schemas.schemas import AttendanceListOut, AttendanceMarkManual, AttendanceMarkQR, AttendanceOut

router = APIRouter()


@router.post("/qr", response_model=AttendanceOut, status_code=201)
def mark_by_qr(payload: AttendanceMarkQR, current_user: User = Depends(get_current_user), db: DBSession = Depends(get_db)):
    session = db.query(Session).filter(Session.qr_token == payload.qr_token, Session.status == SessionStatus.active).first()
    if not session:
        raise HTTPException(status_code=404, detail="Invalid or expired QR token.")
    existing = db.query(AttendanceRecord).filter(
        AttendanceRecord.session_id == session.id,
        AttendanceRecord.student_id == current_user.id
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Attendance already marked.")
    status = AttendanceStatus.present
    if session.started_at:
        cutoff = session.started_at + timedelta(minutes=session.grace_minutes)
        if datetime.utcnow() > cutoff:
            status = AttendanceStatus.late
    record = AttendanceRecord(session_id=session.id, student_id=current_user.id, method=AttendanceMethod.qr, status=status)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.post("/qr-gps-face", response_model=AttendanceOut, status_code=201)
def mark_by_full_flow(payload: AttendanceMarkQR, current_user: User = Depends(get_current_user), db: DBSession = Depends(get_db)):
    """Mark attendance after QR + GPS + Face verification (all done client-side)."""
    session = db.query(Session).filter(Session.qr_token == payload.qr_token, Session.status == SessionStatus.active).first()
    if not session:
        raise HTTPException(status_code=404, detail="Invalid or expired QR token.")
    existing = db.query(AttendanceRecord).filter(
        AttendanceRecord.session_id == session.id,
        AttendanceRecord.student_id == current_user.id
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Attendance already marked.")
    record = AttendanceRecord(
        session_id=session.id,
        student_id=current_user.id,
        method=AttendanceMethod.qr_gps_face,
        status=AttendanceStatus.present
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.post("/manual", response_model=AttendanceOut, status_code=201)
def mark_manual(
    payload: AttendanceMarkManual,
    current_user: User = Depends(require_roles(UserRole.faculty, UserRole.admin)),
    db: DBSession = Depends(get_db),
):
    existing = db.query(AttendanceRecord).filter(
        AttendanceRecord.session_id == payload.session_id,
        AttendanceRecord.student_id == payload.student_id
    ).first()
    if existing:
        existing.status = payload.status
        existing.method = AttendanceMethod.manual
        existing.notes = payload.notes
        db.commit()
        db.refresh(existing)
        return existing
    record = AttendanceRecord(
        session_id=payload.session_id,
        student_id=payload.student_id,
        method=AttendanceMethod.manual,
        status=payload.status,
        notes=payload.notes,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/session/{session_id}", response_model=AttendanceListOut)
def session_attendance(session_id: int, _: User = Depends(require_roles(UserRole.faculty, UserRole.admin)), db: DBSession = Depends(get_db)):
    records = db.query(AttendanceRecord).filter(AttendanceRecord.session_id == session_id).all()
    return {"total": len(records), "records": records}


@router.get("/student/{student_id}", response_model=AttendanceListOut)
def student_history(
    student_id: int,
    course_id: Optional[int] = None,
    skip: int = 0, limit: int = 200,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    if current_user.role == UserRole.student and current_user.id != student_id:
        raise HTTPException(status_code=403, detail="Access denied.")
    q = db.query(AttendanceRecord).filter(AttendanceRecord.student_id == student_id)
    if course_id:
        q = q.join(Session, AttendanceRecord.session_id == Session.id).filter(Session.course_id == course_id)
    total = q.count()
    records = q.order_by(AttendanceRecord.marked_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "records": records}
