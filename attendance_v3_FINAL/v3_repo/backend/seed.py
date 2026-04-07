"""
seed.py - Seeds the database with admin, demo faculty, demo students and courses.
Runs every startup - safe if data already exists.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.database import SessionLocal
from models.models import User, UserRole, UserStatus, Course, SystemSettings
from core.security import hash_password


def main():
    db = SessionLocal()
    print("\n========== SEED STARTING ==========")

    # ── 1. System Settings ──
    try:
        s = db.query(SystemSettings).filter(SystemSettings.id == 1).first()
        if not s:
            db.add(SystemSettings(id=1, gps_range=10, face_required=True, qr_expiry=45,
                                  inst_name="Teerthanker Mahaveer University"))
            db.commit()
            print("Default settings created.")
    except Exception as e:
        print(f"Settings seed error: {e}")
        db.rollback()

    # ── 2. Admin ──
    try:
        if not db.query(User).filter(User.inst_id == "admin1").first():
            db.add(User(
                full_name="System Admin", inst_id="admin1",
                email="admin@smartattendance.com",
                role=UserRole.admin, status=UserStatus.active,
                hashed_password=hash_password("Pass@123"),
                department="Administration",
            ))
            db.commit()
            print("Admin created  →  admin1 / Pass@123")
        else:
            print("Admin already exists.")
    except Exception as e:
        print(f"Admin seed error: {e}")
        db.rollback()

    # ── 3. Demo Faculty ──
    faculty_data = [
        ("Dr. Rajesh Kumar",   "FAC001", "rajesh@tmu.ac.in",  "B.Tech CSE"),
        ("Prof. Meena Sharma", "FAC002", "meena@tmu.ac.in",   "B.Tech ECE"),
    ]
    for name, fid, email, dept in faculty_data:
        try:
            if not db.query(User).filter(User.inst_id == fid).first():
                db.add(User(
                    full_name=name, inst_id=fid, email=email,
                    role=UserRole.faculty, status=UserStatus.active,
                    hashed_password=hash_password("Pass@123"),
                    department=dept,
                ))
                db.commit()
                print(f"Faculty created  →  {fid} / Pass@123")
        except Exception as e:
            print(f"Faculty seed error ({fid}): {e}")
            db.rollback()

    # ── 4. Demo Students ──
    student_data = [
        ("Arjun Singh",  "STU001", "arjun@student.tmu.ac.in",  "B.Tech CSE"),
        ("Priya Gupta",  "STU002", "priya@student.tmu.ac.in",  "B.Tech CSE"),
        ("Ravi Verma",   "STU003", "ravi@student.tmu.ac.in",   "B.Tech ECE"),
        ("Sneha Yadav",  "STU004", "sneha@student.tmu.ac.in",  "B.Tech ECE"),
        ("Amit Sharma",  "STU005", "amit@student.tmu.ac.in",   "BCA"),
    ]
    for name, sid, email, dept in student_data:
        try:
            if not db.query(User).filter(User.inst_id == sid).first():
                db.add(User(
                    full_name=name, inst_id=sid, email=email,
                    role=UserRole.student, status=UserStatus.active,
                    hashed_password=hash_password("Pass@123"),
                    department=dept,
                ))
                db.commit()
                print(f"Student created  →  {sid} / Pass@123")
        except Exception as e:
            print(f"Student seed error ({sid}): {e}")
            db.rollback()

    # ── 5. Demo Courses ──
    course_data = [
        ("CS301", "Data Structures & Algorithms", "B.Tech CSE", 4),
        ("CS302", "Operating Systems",             "B.Tech CSE", 3),
        ("CS303", "Database Management Systems",   "B.Tech CSE", 3),
        ("EC301", "Digital Electronics",           "B.Tech ECE", 4),
        ("BCA201","Web Development",               "BCA",        3),
    ]
    for code, name, dept, credits in course_data:
        try:
            if not db.query(Course).filter(Course.code == code).first():
                db.add(Course(code=code, name=name, department=dept, credits=credits))
                db.commit()
                print(f"Course created  →  {code}: {name}")
        except Exception as e:
            print(f"Course seed error ({code}): {e}")
            db.rollback()

    db.close()
    print("========== SEED COMPLETE ==========\n")


if __name__ == "__main__":
    main()
