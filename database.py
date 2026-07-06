import os
from sqlmodel import SQLModel, create_engine, Session
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # 👈 Mengetuk pintu sebelum masuk
    pool_recycle=300     # 👈 Mereset koneksi setiap 5 menit (300 detik) agar tidak diputus paksa Neon
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# Cara profesional mengambil sesi database
def get_session():
    with Session(engine) as session:
        yield session

# Fungsi wajib ini yang harus dipanggil di setiap rute FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() # <--- INI VITAL! Menutup koneksi otomatis