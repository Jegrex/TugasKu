import asyncio
from fastapi import FastAPI
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from database import create_db_and_tables
from routers import auth, tugas
from bot import start_bot  # Memanggil fungsi bot kita

# ==========================================
# MANAJER SIKLUS HIDUP APLIKASI (LIFESPAN)
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Saat Server Menyala: Buat tabel & Jalankan Bot di latar belakang
    create_db_and_tables()
    asyncio.create_task(start_bot())
    yield
    # 2. Saat Server Mati: (Kosongkan saja untuk saat ini)
    pass

# Inisialisasi Aplikasi dengan Lifespan
app = FastAPI(lifespan=lifespan)

# Mendaftarkan Rute API
app.include_router(auth.router)
app.include_router(tugas.router)

# Rute Halaman Web
@app.get("/")
def tampilkan_web():
    return FileResponse("templates/index.html")