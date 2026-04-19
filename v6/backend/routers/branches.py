"""Branch listing routes."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session as DBSession

from core.branches import ensure_default_branches_for_course
from db.database import get_db
from models.models import Branch

router = APIRouter()


@router.get("")
def list_branches(
    course: str = Query(..., min_length=1),
    db: DBSession = Depends(get_db),
):
    course_name = course.strip()
    if not course_name:
        return {"course": "", "branches": []}
    ensure_default_branches_for_course(db, course_name)
    db.commit()
    rows = (
        db.query(Branch.branch)
        .filter(Branch.course == course_name)
        .order_by(Branch.branch.asc())
        .all()
    )
    return {"course": course_name, "branches": [row[0] for row in rows]}

