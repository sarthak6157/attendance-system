"""Timetable routes — admin creates slots, faculty goes live."""
from datetime import datetime
import secrets
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DBSession

from core.security import get_current_user, require_roles
from db.database import get_db
from models.models import TimetableSlot, Session, SessionStatus, User, UserRole, Course, DayOfWeek
from pydantic import BaseModel

router = APIRouter()
AdminOnly      = require_roles(UserRole.admin)
FacultyOrAdmin = require_roles(UserRole.faculty, UserRole.admin)


# ── Schemas ──────────────────────────────────────────────────────────────────

class SlotCreate(BaseModel):
    course_id:   int
    faculty_id:  int
    day_of_week: str
    start_time:  str
    end_time:    str
    room:        Optional[str] = None
    branch:      Optional[str] = None
    section:     Optional[str] = None
    semester:    Optional[str] = None
    course_type: Optional[str] = None

class SlotOut(BaseModel):
    id:          int
    course_id:   int
    faculty_id:  int
    day_of_week: str
    start_time:  str
    end_time:    str
    room:        Optional[str]
    branch:      Optional[str]
    section:     Optional[str]
    semester:    Optional[str]
    course_type: Optional[str]
    is_active:   bool
    course_name: Optional[str] = None
    faculty_name:Optional[str] = None
    class Config:
        from_attributes = True

class GoLiveRequest(BaseModel):
    gps_lat: Optional[str] = None
    gps_lng: Optional[str] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

# ⚠️ /debug/student-match MUST be before /{slot_id} routes to avoid 404

@router.get("/debug/student-match")
def debug_student_match(
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    from sqlalchemy import distinct
    all_branches = db.query(distinct(TimetableSlot.branch)).all()
    all_sections = db.query(distinct(TimetableSlot.section)).all()
    return {
        "student_branch":      current_user.branch,
        "student_department":  current_user.department,
        "student_section":     current_user.section,
        "timetable_branches":  [r[0] for r in all_branches],
        "timetable_sections":  [r[0] for r in all_sections],
    }


@router.get("", response_model=List[SlotOut])
def list_slots(
    branch:     Optional[str] = Query(None),
    section:    Optional[str] = Query(None),
    faculty_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    from sqlalchemy import func, or_
    q = db.query(TimetableSlot).filter(TimetableSlot.is_active == True)

    if current_user.role == UserRole.faculty:
        q = q.filter(TimetableSlot.faculty_id == current_user.id)
    elif faculty_id:
        q = q.filter(TimetableSlot.faculty_id == faculty_id)

    # For students: auto-inject their branch/section if not passed
    if current_user.role == UserRole.student:
        effective_branch  = branch  or current_user.branch or current_user.department
        effective_section = section or current_user.section
    else:
        effective_branch  = branch
        effective_section = section

    # Case-insensitive branch match
    if effective_branch:
        q = q.filter(func.lower(TimetableSlot.branch) == effective_branch.strip().lower())

    # For students with sub-group (e.g. A1, A2):
    # Show BOTH their sub-group slots (labs) AND parent section slots (theory)
    # e.g. student in A1 sees section="A1" labs AND section="A" theory classes
    if effective_section:
        s = effective_section.strip().upper()
        parent = s[0] if len(s) > 1 else None  # "A1" → "A", "B2" → "B"
        if parent and current_user.role == UserRole.student:
            q = q.filter(or_(
                func.lower(TimetableSlot.section) == s.lower(),
                func.lower(TimetableSlot.section) == parent.lower()
            ))
        else:
            q = q.filter(func.lower(TimetableSlot.section) == s.lower())

    slots = q.order_by(TimetableSlot.day_of_week, TimetableSlot.start_time).all()
    result = []
    for s in slots:
        co  = db.query(Course).filter(Course.id == s.course_id).first()
        fac = db.query(User).filter(User.id == s.faculty_id).first()
        d = SlotOut.model_validate(s)
        d.course_name  = co.name  if co  else None
        d.faculty_name = fac.full_name if fac else None
        result.append(d)
    return result


@router.post("", response_model=SlotOut, status_code=201)
def create_slot(
    payload: SlotCreate,
    _: User = Depends(AdminOnly),
    db: DBSession = Depends(get_db),
):
    co  = db.query(Course).filter(Course.id == payload.course_id).first()
    fac = db.query(User).filter(User.id == payload.faculty_id, User.role == UserRole.faculty).first()
    if not co:  raise HTTPException(status_code=404, detail="Course not found.")
    if not fac: raise HTTPException(status_code=404, detail="Faculty not found.")
    slot = TimetableSlot(**payload.model_dump())
    db.add(slot); db.commit(); db.refresh(slot)
    d = SlotOut.model_validate(slot)
    d.course_name = co.name; d.faculty_name = fac.full_name
    return d


@router.delete("/{slot_id}", status_code=204)
def delete_slot(slot_id: int, _: User = Depends(AdminOnly), db: DBSession = Depends(get_db)):
    slot = db.query(TimetableSlot).filter(TimetableSlot.id == slot_id).first()
    if not slot: raise HTTPException(status_code=404)
    db.delete(slot); db.commit()


@router.post("/{slot_id}/go-live")
def go_live(
    slot_id: int,
    payload: GoLiveRequest,
    current_user: User = Depends(FacultyOrAdmin),
    db: DBSession = Depends(get_db),
):
    """Faculty clicks Go Live on a timetable slot → creates active session."""
    slot = db.query(TimetableSlot).filter(TimetableSlot.id == slot_id, TimetableSlot.is_active == True).first()
    if not slot: raise HTTPException(status_code=404, detail="Timetable slot not found.")
    if current_user.role != UserRole.admin and slot.faculty_id != current_user.id:
        raise HTTPException(status_code=403, detail="This slot belongs to another faculty.")
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    existing = db.query(Session).filter(
        Session.timetable_id == slot_id,
        Session.status == SessionStatus.active,
        Session.created_at >= today_start,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="This class is already live today.")
    co = db.query(Course).filter(Course.id == slot.course_id).first()
    now = datetime.utcnow()
    session = Session(
        course_id    = slot.course_id,
        faculty_id   = slot.faculty_id,
        timetable_id = slot.id,
        title        = f"{co.name if co else 'Class'} — {slot.day_of_week} {slot.start_time}",
        location     = slot.room,
        branch       = slot.branch,
        section      = slot.section,
        semester     = slot.semester,
        course_type  = slot.course_type,
        gps_lat      = payload.gps_lat,
        gps_lng      = payload.gps_lng,
        status       = SessionStatus.active,
        scheduled_at = now,
        started_at   = now,
        qr_token     = secrets.token_urlsafe(16),
        grace_minutes= 15,
    )
    db.add(session); db.commit(); db.refresh(session)
    return {"session_id": session.id, "qr_token": session.qr_token, "message": "Session is now live!"}
