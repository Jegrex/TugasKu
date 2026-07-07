from sqlmodel import SQLModel, Field
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    password_hash: str
    telegram_id: Optional[str] = None

class Tugas(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    mata_kuliah: str
    deskripsi: str
    deadline: datetime
    prioritas: str
    is_selesai: bool = False

    is_diingatkan_h3: bool = False
    is_diingatkan_h2: bool = False
    is_diingatkan_h1: bool = False
    owner_id: Optional[int] = Field(default=None, foreign_key="user.id")

class UserCreate(BaseModel):
    username: str
    password: str
    telegram_id: Optional[str] = None