"""Users routes: admin creates/manages all users."""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.security import get_current_user, hash_password, require_roles
from db.database import get_db
from models.models import User, UserRole, UserStatus
from schemas.schemas import UserCreate, UserListOut, UserOut, UserStatusUpdate, UserUpdate

router = APIRouter()
AdminOnly      = require_roles(UserRole.admin)
AdminOrFaculty = require_roles(UserRole.admin, UserRole.faculty)


@router.get("", response_model=UserListOut)
def list_users(
    role:     Optional[str] = Query(None),
    status_:  Optional[str] = Query(None, alias="status"),
    search:   Optional[str] = Query(None),
    skip:     int = Query(0, ge=0),
    limit:    int = Query(100, ge=1, le=500),
    _:        User = Depends(AdminOrFaculty),
    db:       Session = Depends(get_db),
):
    q = db.query(User)
    if role:
        q = q.filter(User.role == role)
    if status_:
        q = q.filter(User.status == status_)
    if search:
        like = f"%{search}%"
        q = q.filter(
            User.full_name.ilike(like) | User.email.ilike(like) | User.inst_id.ilike(like)
        )
    total = q.count()
    users = q.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "users": users}


@router.post("", response_model=UserOut, status_code=201)
def admin_create_user(
    payload: UserCreate,
    _:  User    = Depends(AdminOnly),
    db: Session = Depends(get_db),
):
    """Admin creates users with any role — immediately active."""
    existing = db.query(User).filter(
        (User.inst_id == payload.inst_id) | (User.email == payload.email)
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="User with this ID or email already exists.")
    new_user = User(
        full_name=payload.full_name,
        inst_id=payload.inst_id,
        email=payload.email,
        role=payload.role,
        status=UserStatus.active,   # admin-created users are immediately active
        hashed_password=hash_password(payload.password),
        department=payload.department,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied.")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied.")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(user, field, value)
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}/status", response_model=UserOut)
def update_status(
    user_id: int,
    payload: UserStatusUpdate,
    _:  User    = Depends(AdminOnly),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user.status = payload.status
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    current_admin: User = Depends(AdminOnly),
    db: Session = Depends(get_db),
):
    if user_id == current_admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account.")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    db.delete(user)
    db.commit()
