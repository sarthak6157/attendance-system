"""Branch helpers: normalization, defaults, and persistence."""
from typing import Optional

from sqlalchemy.orm import Session

from models.models import Branch

DEFAULT_BRANCH_MAP: dict[str, list[str]] = {
    "B.Tech": [
        "CSE (Computer Science & Engineering)",
        "ECE (Electronics & Communication)",
        "ME (Mechanical Engineering)",
        "Civil Engineering",
        "EE (Electrical Engineering)",
        "IT (Information Technology)",
        "Chemical Engineering",
        "Biotechnology",
        "Aerospace Engineering",
    ],
    "B.E": ["CSE", "ECE", "ME", "Civil", "EE", "IT", "Chemical", "Biotechnology"],
    "BCA": ["BCA (General)", "BCA with Data Science", "BCA with Cybersecurity"],
    "MCA": ["MCA (General)", "MCA with AI/ML", "MCA with Cloud Computing"],
    "MBA": ["Finance", "Marketing", "Human Resource", "Operations", "Business Analytics", "International Business"],
    "B.Pharma": ["B.Pharma (General)", "Pharmaceutical Chemistry", "Pharmacology"],
    "M.Tech": ["CSE", "ECE", "ME", "Civil", "AI & Machine Learning", "Data Science", "VLSI Design"],
    "B.Sc": ["Physics", "Chemistry", "Mathematics", "Biology", "Computer Science", "Statistics"],
    "M.Sc": ["Physics", "Chemistry", "Mathematics", "Biology", "Computer Science"],
    "BBA": ["BBA (General)", "BBA Finance", "BBA Marketing", "BBA HR"],
    "B.Com": ["B.Com (General)", "B.Com Hons", "B.Com with CA"],
    "LLB": ["LLB (General)", "LLB (Corporate Law)", "LLB (Criminal Law)"],
    "MBBS": ["MBBS (General Medicine)"],
}


def normalize_branch_name(course: Optional[str], branch: Optional[str]) -> Optional[str]:
    if not branch:
        return None
    value = branch.strip()
    if not value:
        return None
    if course:
        c = course.strip()
        if not c:
            return value
        prefix = f"{c} - "
        if value.lower().startswith(prefix.lower()):
            value = value[len(prefix):].strip()
        if value.lower() == c.lower():
            return None
    return value or None


def upsert_branch(db: Session, course: Optional[str], branch: Optional[str]) -> None:
    course_name = (course or "").strip()
    branch_name = normalize_branch_name(course_name, branch)
    if not course_name or not branch_name:
        return
    existing = db.query(Branch).filter(Branch.course == course_name, Branch.branch == branch_name).first()
    if not existing:
        db.add(Branch(course=course_name, branch=branch_name))


def ensure_default_branches_for_course(db: Session, course: Optional[str]) -> None:
    course_name = (course or "").strip()
    if not course_name:
        return
    for branch in DEFAULT_BRANCH_MAP.get(course_name, []):
        upsert_branch(db, course_name, branch)

