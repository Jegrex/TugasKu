from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from datetime import datetime, timedelta
from database import get_session
from models import User, UserCreate
from security import get_password_hash, verify_password, create_access_token
from pydantic import BaseModel

# Membuat pengelompokan API (Router)
router = APIRouter(prefix="/api", tags=["Auth"])

@router.post("/register")
def register_user(user_data: UserCreate, session: Session = Depends(get_session)):
    existing_user = session.exec(select(User).where(User.username == user_data.username)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username sudah dipakai.")
    
    hashed_pw = get_password_hash(user_data.password)
    new_user = User(username=user_data.username, password_hash=hashed_pw, telegram_id=user_data.telegram_id)
    
    session.add(new_user)
    session.commit()
    return {"message": "Registrasi berhasil! Silakan login."}

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Username atau password salah")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

from security import get_current_user # Tambahkan di area import atas jika belum ada

# API Untuk Mengambil Data User yang Sedang Login
@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "username": current_user.username,
        "telegram_id": current_user.telegram_id
    }

class TelegramUpdate(BaseModel):
    telegram_id: str

@router.put("/me/telegram")
def update_telegram(data: TelegramUpdate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    current_user.telegram_id = data.telegram_id
    session.add(current_user)
    session.commit()
    return {"message": "Telegram ID berhasil diupdate"}