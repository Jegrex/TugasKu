import asyncio
import os
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandObject
from sqlmodel import Field, Session, SQLModel, create_engine, select
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
# Tambahkan Request di baris ini
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates # Tambahkan baris baru ini

load_dotenv()

# ==========================================
# 1. KONFIGURASI UTAMA
# ==========================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_USER_ID = int(os.getenv("TARGET_USER_ID"))

# Ambil URL PostgreSQL dari file .env
DATABASE_URL = os.getenv("DATABASE_URL")

# Buat engine SQLModel untuk PostgreSQL (tidak perlu connect_args check_same_thread lagi seperti SQLite)
engine = create_engine(DATABASE_URL)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

scheduler = AsyncIOScheduler()

# ==========================================
# 2. MODEL DATABASE
# ==========================================
class Tugas(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    mata_kuliah: str
    deskripsi: str
    deadline: str
    is_selesai: bool = Field(default=False)

def inisialisasi_database():
    SQLModel.metadata.create_all(engine)


# ==========================================
# 3. FUNGSI PENJADWAL OTOMATIS (CRON JOB)
# ==========================================
# Tambahkan kata 'async' di depan def
async def kirim_pengingat_otomatis():
    """Fungsi ini akan dipicu otomatis oleh Scheduler untuk membroadcast tugas"""
    print("[SCHEDULING] Mengecek tugas untuk pengingat otomatis...")
    
    with Session(engine) as session:
        statement = select(Tugas).where(Tugas.is_selesai == False)
        daftar_tugas = session.exec(statement).all()
        
        if daftar_tugas:
            teks_pengingat = "⏰ **PENGINGAT OTOMATIS: Jangan Lupa Tugas Kamu!**\n\n"
            for i, tugas in enumerate(daftar_tugas, 1):
                teks_pengingat += (
                    f"{i}. 📖 **{tugas.mata_kuliah}**\n"
                    f"   🗓️ Deadline: {tugas.deadline}\n"
                    f"   📝 Detail: {tugas.deskripsi}\n\n"
                )
            teks_pengingat += "Semangat kuliahnya! Kerjakan sekarang biar tenang nanti. 💪"
            
            # Ganti asyncio.run menjadi await langsung
            await bot.send_message(chat_id=TARGET_USER_ID, text=teks_pengingat, parse_mode="Markdown")
            print(f"[SCHEDULING] Pengingat sukses dikirim ke user {TARGET_USER_ID}")
        else:
            print("[SCHEDULING] Tidak ada tugas aktif, pengingat tidak dikirim.")


# ==========================================
# 4. LOGIKA BOT TELEGRAM (MANUAL)
# ==========================================
@dp.message(Command("start"))
async def perintah_start(message: types.Message):
    # Log ke terminal untuk tahu ID Telegram Anda saat start jika belum tahu
    print(f"User {message.from_user.first_name} memulai bot. ID Telegram: {message.from_user.id}")
    await message.reply("Halo! Bot Pengingat Tugas Aktif. Tugas kamu akan diingatkan otomatis secara berkala.")

@dp.message(Command("tugas"))
async def perintah_tugas(message: types.Message):
    with Session(engine) as session:
        statement = select(Tugas).where(Tugas.is_selesai == False)
        daftar_tugas = session.exec(statement).all()

        if not daftar_tugas:
            await message.reply("🎉 Hore! Tidak ada tugas aktif saat ini.")
            return

        teks_balasan = "📚 **Daftar Tugas Aktif Kamu:**\n\n"
        for i, tugas in enumerate(daftar_tugas, 1):
            teks_balasan += f"{i}. 📖 **{tugas.mata_kuliah}**\n   🗓️ Deadline: {tugas.deadline}\n\n"
        await message.reply(teks_balasan, parse_mode="Markdown")

@dp.message(Command("selesai"))
async def perintah_selesai(message: types.Message, command: CommandObject):
    # 1. Validasi apakah pengguna memasukkan argumen angka setelah perintah /selesai
    if not command.args:
        await message.reply(
            "❌ Format salah! Silakan masukkan ID tugas setelah perintah.\n"
            "Contoh: `/selesai 1`", 
            parse_mode="Markdown"
        )
        return
    
    # 2. Pastikan argumen yang dimasukkan adalah angka valid
    try:
        tugas_id = int(command.args)
    except ValueError:
        await message.reply("❌ ID tugas harus berupa angka. Contoh: `/selesai 1`")
        return

    # 3. Proses mengubah data di database SQLite
    with Session(engine) as session:
        # Cari tugas berdasarkan ID-nya
        tugas = session.get(Tugas, tugas_id)
        
        # Jika tugas tidak ditemukan
        if not tugas:
            await message.reply(f"❌ Tugas dengan ID {tugas_id} tidak ditemukan di database.")
            return
        
        # Jika tugas ternyata sudah diselesaikan sebelumnya
        if tugas.is_selesai:
            await message.reply(f"✅ Tugas *{tugas.mata_kuliah}* memang sudah selesai sebelumnya.", parse_mode="Markdown")
            return
        
        # Ubah status tugas menjadi selesai (True)
        tugas.is_selesai = True
        session.add(tugas)
        session.commit()
        
        await message.reply(
            f"🎉 **Hebat!** Tugas *{tugas.mata_kuliah}* berhasil ditandai selesai.\n"
            f"Bot tidak akan mengirimkan pengingat untuk tugas ini lagi.", 
            parse_mode="Markdown"
        )



# ==========================================
# 5. INTEGRASI FASTAPI & LIFESPAN
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Saat Server MULAI
    inisialisasi_database()
    
    # Konfigurasi Scheduler: Jalankan fungsi setiap 30 detik untuk simulasi/testing awal
    # Di dunia nyata, ini bisa diatur menjadi: trigger='cron', hour=7, minute=0 (setiap jam 7 pagi)
    scheduler.add_job(kirim_pengingat_otomatis, trigger='interval', seconds=30)
    scheduler.start()
    print("[SISTEM] Scheduler Otomatis Dimulai...")
    
    print("[SISTEM] Memulai Bot Telegram...")
    polling_task = asyncio.create_task(dp.start_polling(bot))
    
    yield
    
    # Saat Server MATI
    print("[SISTEM] Menghentikan Scheduler & Bot...")
    scheduler.shutdown()
    await bot.session.close()
    polling_task.cancel()

app = FastAPI(title="API Pengingat Tugas Mahasiswa", version="1.2.0", lifespan=lifespan)


# ==========================================
# 6. ENDPOINT API & WEB DASHBOARD
# ==========================================
# Beri tahu FastAPI letak folder HTML kita
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def home(request: Request):
    # Memanggil parameter secara eksplisit (request=..., name=...) agar sesuai versi terbaru
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"request": request}
    )

# (Kode @app.get("/api/tugas") dan seterusnya tetap biarkan seperti aslinya)
# Endpoint untuk mengambil daftar tugas ke tabel web
@app.get("/api/tugas")
def ambil_semua_tugas_api():
    with Session(engine) as session:
        tugas = session.exec(select(Tugas)).all()
        return tugas

# Endpoint untuk menyimpan tugas baru dari form web
@app.post("/api/tugas")
def tambah_tugas_api(tugas_baru: Tugas):
    with Session(engine) as session:
        session.add(tugas_baru)
        session.commit()
        session.refresh(tugas_baru)
        return {"status": "sukses", "data_tersimpan": tugas_baru}