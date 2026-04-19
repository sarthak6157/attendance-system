"""Auth routes: login, register, profile, change-password, forgot-password OTP."""
import random, string
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.security import create_access_token, get_current_user, hash_password, verify_password
from db.database import get_db
from models.models import User, UserRole, UserStatus
from schemas.schemas import LoginRequest, PasswordChangeRequest, TokenResponse, UserCreate, UserOut, UserUpdate

router = APIRouter()
_otp_store: dict = {}

def _send_email(to_email: str, otp: str) -> bool:
    import os, smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    gmail_user = os.getenv("GMAIL_USER","")
    gmail_pass = os.getenv("GMAIL_APP_PASSWORD","")
    if not gmail_user or not gmail_pass:
        print(f"[DEV] OTP for {to_email}: {otp}")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Password Reset OTP — Smart Attendance TMU"
        msg["From"] = f"Smart Attendance TMU <{gmail_user}>"
        msg["To"] = to_email
        html = f"""<div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;">
          <div style="background:#1a3c6e;padding:20px;border-radius:8px 8px 0 0;text-align:center;">
            <h2 style="color:#fff;margin:0;">Smart Attendance — TMU</h2></div>
          <div style="background:#fff;padding:28px;border-radius:0 0 8px 8px;border:1px solid #dde3ef;">
            <h3 style="color:#1a3c6e;">Your Password Reset OTP</h3>
            <p style="color:#555;">Use the OTP below — expires in <strong>10 minutes</strong>.</p>
            <div style="background:#f0f4fa;border:2px dashed #1a3c6e;border-radius:10px;padding:20px;text-align:center;margin:20px 0;">
              <div style="font-size:2.4rem;font-weight:800;letter-spacing:10px;color:#1a3c6e;">{otp}</div></div>
            <p style="color:#aaa;font-size:.82rem;">If you did not request this, ignore this email.</p></div></div>"""
        msg.attach(MIMEText(otp,"plain")); msg.attach(MIMEText(html,"html"))
        with smtplib.SMTP_SSL("smtp.gmail.com",465) as smtp:
            smtp.login(gmail_user,gmail_pass); smtp.sendmail(gmail_user,to_email,msg.as_string())
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] {e}"); return False

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    credential = payload.credential.strip()
    user = db.query(User).filter((User.email==credential)|(User.inst_id==credential)).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    if user.status == UserStatus.pending:
        raise HTTPException(status_code=403, detail="Account pending admin approval.")
    if user.status == UserStatus.inactive:
        raise HTTPException(status_code=403, detail="Account is deactivated. Contact admin.")
    user.last_login = datetime.utcnow(); db.commit()
    token = create_access_token({"sub": user.id, "role": user.role.value})
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))

@router.post("/register", response_model=UserOut, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter((User.inst_id==payload.inst_id)|(User.email==payload.email)).first()
    if existing:
        raise HTTPException(status_code=409, detail="User with this ID or email already exists.")
    dept = payload.department or payload.branch or ''
    new_user = User(
        full_name=payload.full_name, inst_id=payload.inst_id, email=payload.email,
        role=UserRole.student, status=UserStatus.pending,
        hashed_password=hash_password(payload.password), department=dept,
        branch=payload.branch or payload.department or '',
        section=getattr(payload,'section',None), semester=getattr(payload,'semester',None),
        course=getattr(payload,'course_type',None),
    )
    db.add(new_user); db.commit(); db.refresh(new_user)
    return new_user

@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user

@router.patch("/me", response_model=UserOut)
def update_me(payload: UserUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(current_user, field, value)
    current_user.updated_at = datetime.utcnow(); db.commit(); db.refresh(current_user)
    return current_user

@router.post("/change-password", status_code=200)
def change_password(payload: PasswordChangeRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=401, detail="Current password is incorrect.")
    current_user.hashed_password = hash_password(payload.new_password)
    current_user.updated_at = datetime.utcnow(); db.commit()
    return {"message": "Password updated successfully."}

@router.post("/forgot-password/send-otp")
def send_otp(payload: dict, db: Session = Depends(get_db)):
    import os
    email = (payload.get("email") or "").strip().lower()
    if not email: raise HTTPException(status_code=400, detail="Email is required.")
    user = db.query(User).filter((User.email==email)|(User.inst_id==email)).first()
    if not user: return {"message": "If this email is registered, an OTP has been sent."}
    otp = ''.join(random.choices(string.digits, k=6))
    _otp_store[user.email] = {"otp":otp,"expires_at":datetime.utcnow()+timedelta(minutes=10),"user_id":user.id,"attempts":0}
    sent = _send_email(user.email, otp)
    if not os.getenv("GMAIL_USER"):
        return {"message":"OTP sent (dev mode).","dev_otp":otp,"email":user.email}
    return {"message":"OTP sent to registered email.","email_sent":sent}

@router.post("/forgot-password/verify-otp")
def verify_otp(payload: dict):
    email = (payload.get("email") or "").strip().lower()
    otp   = (payload.get("otp") or "").strip()
    record = _otp_store.get(email)
    if not record: raise HTTPException(status_code=400, detail="No OTP found. Please request a new one.")
    if datetime.utcnow() > record["expires_at"]:
        _otp_store.pop(email,None); raise HTTPException(status_code=400, detail="OTP has expired.")
    record["attempts"] = record.get("attempts",0)+1
    if record["attempts"] > 5:
        _otp_store.pop(email,None); raise HTTPException(status_code=429, detail="Too many attempts. Request a new OTP.")
    if record["otp"] != otp:
        raise HTTPException(status_code=400, detail=f"Invalid OTP. {5-record['attempts']} attempts left.")
    reset_token = ''.join(random.choices(string.ascii_letters+string.digits, k=32))
    record["reset_token"]=reset_token; record["verified"]=True
    return {"message":"OTP verified.","reset_token":reset_token}

@router.post("/forgot-password/reset")
def reset_password(payload: dict, db: Session = Depends(get_db)):
    email       = (payload.get("email") or "").strip().lower()
    reset_token = (payload.get("reset_token") or "").strip()
    new_password = payload.get("new_password") or ""
    if len(new_password)<6: raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")
    record = _otp_store.get(email)
    if not record or not record.get("verified") or record.get("reset_token")!=reset_token:
        raise HTTPException(status_code=400, detail="Invalid or expired reset session.")
    user = db.query(User).filter(User.id==record["user_id"]).first()
    if not user: raise HTTPException(status_code=404, detail="User not found.")
    user.hashed_password=hash_password(new_password); user.updated_at=datetime.utcnow()
    db.commit(); _otp_store.pop(email,None)
    return {"message":"Password reset successfully."}
