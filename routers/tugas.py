from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List

from database import get_session
from models import Tugas, User
from security import get_current_user

router = APIRouter(prefix="/api/tugas", tags=["Tugas"])

@router.get("/")
def get_tugas(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    tugas = session.exec(select(Tugas).where(Tugas.owner_id == current_user.id)).all()
    return tugas

@router.post("/")
def tambah_tugas(tugas_baru: Tugas, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    tugas_baru.owner_id = current_user.id
    session.add(tugas_baru)
    session.commit()
    session.refresh(tugas_baru)
    return tugas_baru

@router.delete("/{tugas_id}")
def hapus_tugas(tugas_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    tugas = session.exec(
        select(Tugas).where(Tugas.id == tugas_id, Tugas.owner_id == current_user.id)
    ).first()
    
    if not tugas:
        raise HTTPException(status_code=404, detail="Tugas tidak ditemukan/bukan milik Anda")
        
    session.delete(tugas)
    session.commit()
    return {"message": "Tugas berhasil dihapus"}

# MENGUBAH TUGAS (Termasuk menandai selesai)
@router.put("/{tugas_id}")
def update_tugas(tugas_id: int, tugas_update: Tugas, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    # Cari tugas milik user ini
    tugas = session.exec(select(Tugas).where(Tugas.id == tugas_id, Tugas.owner_id == current_user.id)).first()
    
    if not tugas:
        raise HTTPException(status_code=404, detail="Tugas tidak ditemukan")
        
    # Update datanya
    tugas.mata_kuliah = tugas_update.mata_kuliah
    tugas.deskripsi = tugas_update.deskripsi
    tugas.deadline = tugas_update.deadline
    tugas.prioritas = tugas_update.prioritas
    tugas.is_selesai = tugas_update.is_selesai
    
    session.add(tugas)
    session.commit()
    session.refresh(tugas)
    return tugas