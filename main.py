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
from datetime import datetime, timedelta
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
    id: int | None = Field(default=None, primary_key=True)
    mata_kuliah: str
    deskripsi: str
    deadline: datetime
    is_selesai: bool = Field(default=False)
    # Kolom baru untuk tingkat prioritas (Tinggi, Sedang, Rendah)
    prioritas: str = Field(default="Sedang") 
    # Tiga sakelar alarm untuk melacak riwayat pengingat
    is_diingatkan_h3: bool = Field(default=False)
    is_diingatkan_h2: bool = Field(default=False)
    is_diingatkan_h1: bool = Field(default=False)

def inisialisasi_database():
    SQLModel.metadata.create_all(engine)

# ==========================================
# BOT FEATURE: DAILY MORNING BRIEFING
# ==========================================

async def kirim_briefing_pagi():
    with Session(engine) as session:
        # 1. Ambil semua tugas yang belum selesai
        tugas_aktif = session.exec(
            select(Tugas).where(Tugas.is_selesai == False)
        ).all()
        
        total_aktif = len(tugas_aktif)
        
        # Jika tidak ada tugas sama sekali, beri kabar gembira
        if total_aktif == 0:
            pesan = (
                "☀️ <b>DAILY MORNING BRIEFING</b> ☀️\n\n"
                "Selamat pagi! Hari ini kalender tugas Anda benar-benar bersih. "
                "Tidak ada tugas aktif yang menanti. Nikmati hari santai Anda! 🎉"
            )
            await bot.send_message(chat_id=TARGET_USER_ID, text=pesan, parse_mode="HTML")
            return

        # 2. Hitung statistik berdasarkan prioritas tugas
        tinggi = len([t for t in tugas_aktif if t.prioritas == "Tinggi"])
        sedang = len([t for t in tugas_aktif if t.prioritas == "Sedang"])
        rendah = len([t for t in tugas_aktif if t.prioritas == "Rendah"])
        
        # Ambil daftar khusus untuk tugas prioritas tinggi
        tugas_tinggi = [t for t in tugas_aktif if t.prioritas == "Tinggi"]
        
        # 3. Susun template pesan laporan pagi
        pesan = (
            f"☀️ <b>DAILY MORNING BRIEFING</b> ☀️\n\n"
            f"Selamat pagi! Berikut adalah rekapitulasi tugas kuliah Anda hari ini:\n\n"
            f"📊 <b>Ringkasan Tugas:</b>\n"
            f"• Total Tugas Aktif: <b>{total_aktif}</b> tugas\n\n"
            f"🚨 <b>Berdasarkan Tingkat Kepentingan:</b>\n"
            f"• 🔴 Tinggi: {tinggi} tugas\n"
            f"• 🟡 Sedang: {sedang} tugas\n"
            f"• ⚪ Rendah: {rendah} tugas\n\n"
        )
        
        # Jika ada tugas prioritas tinggi, jabarkan daftarnya agar menjadi fokus utama
        if tinggi > 0:
            pesan += "⚠️ <b>Fokus Utama Hari Ini (Prioritas Tinggi):</b>\n"
            for idx, t in enumerate(tugas_tinggi, 1):
                pesan += f"{idx}. <b>[{t.mata_kuliah}]</b> {t.deskripsi}\n   ⏱️ Deadline: {t.deadline.strftime('%d %b %Y, %H:%M')}\n"
            pesan += "\n"
            
        pesan += "Mari susun skala prioritas dan cicil tugas Anda hari ini. Tetap semangat! 💪"
        
        # 4. Tembakkan ke Telegram pribadi Anda
        await bot.send_message(chat_id=TARGET_USER_ID, text=pesan, parse_mode="HTML")


# ==========================================
# 3. FUNGSI PENJADWAL OTOMATIS (CRON JOB)
# ==========================================
# Tambahkan kata 'async' di depan def
async def kirim_pengingat_otomatis():
    with Session(engine) as session:
        # Hanya ambil tugas yang BELUM selesai
        tugas_aktif = session.exec(select(Tugas).where(Tugas.is_selesai == False)).all()
        waktu_sekarang = datetime.now()

        for tugas in tugas_aktif:
            # Hitung jarak waktu dari sekarang ke deadline
            selisih = tugas.deadline - waktu_sekarang

            # =======================================================
            # LOGIKA KHUSUS: TUGAS PRIORITAS TINGGI (H-3, H-2, H-1)
            # =======================================================
            if tugas.prioritas == "Tinggi":
                
                # --- PENGINGAT H-3 (Antara 48 jam hingga 72 jam sebelum deadline) ---
                if timedelta(hours=48) < selisih <= timedelta(hours=72) and not tugas.is_diingatkan_h3:
                    pesan = f"🚨 <b>PENGINGAT H-3: TUGAS UTAMA!</b> 🚨\n\nKategori: {tugas.mata_kuliah}\nTugas: {tugas.deskripsi}\nDeadline: {tugas.deadline.strftime('%d %b %Y, %H:%M')}\n\n<i>Tugas ini berprioritas tinggi. Jangan lupa dicicil ya!</i>"
                    await bot.send_message(chat_id=TARGET_USER_ID, text=pesan, parse_mode="HTML")
                    tugas.is_diingatkan_h3 = True

                # --- PENGINGAT H-2 (Antara 24 jam hingga 48 jam sebelum deadline) ---
                elif timedelta(hours=24) < selisih <= timedelta(hours=48) and not tugas.is_diingatkan_h2:
                    pesan = f"⚠️ <b>PENGINGAT H-2: TUGAS UTAMA!</b> ⚠️\n\nKategori: {tugas.mata_kuliah}\nTugas: {tugas.deskripsi}\nDeadline: {tugas.deadline.strftime('%d %b %Y, %H:%M')}\n\n<i>Waktu berjalan terus. Pastikan progres tugas ini aman!</i>"
                    await bot.send_message(chat_id=TARGET_USER_ID, text=pesan, parse_mode="HTML")
                    tugas.is_diingatkan_h2 = True

                # --- PENGINGAT H-1 (Kurang dari 24 jam sebelum deadline) ---
                elif timedelta(hours=0) < selisih <= timedelta(hours=24) and not tugas.is_diingatkan_h1:
                    pesan = f"🔥 <b>PENGINGAT H-1: BESOK DEADLINE!</b> 🔥\n\nKategori: {tugas.mata_kuliah}\nTugas: {tugas.deskripsi}\nDeadline: {tugas.deadline.strftime('%d %b %Y, %H:%M')}\n\n<i>Kesempatan terakhir! Segera selesaikan dan kumpulkan!</i>"
                    await bot.send_message(chat_id=TARGET_USER_ID, text=pesan, parse_mode="HTML")
                    tugas.is_diingatkan_h1 = True



            # =======================================================
            # LOGIKA NORMAL: TUGAS SEDANG / RENDAH (H-1 SAJA)
            # =======================================================
            else:
                if timedelta(hours=0) < selisih <= timedelta(hours=24) and not tugas.is_diingatkan_h1:
                    pesan = f"🔔 <b>PENGINGAT DEADLINE H-1</b> 🔔\n\nKategori: {tugas.mata_kuliah}\nTugas: {tugas.deskripsi}\nDeadline: {tugas.deadline.strftime('%d %b %Y, %H:%M')}"
                    await bot.send_message(chat_id=TARGET_USER_ID, text=pesan, parse_mode="HTML")
                    tugas.is_diingatkan_h1 = True

            # Simpan setiap perubahan status alarm ke database
            session.add(tugas)
        
        session.commit()


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
    # 1. TUGAS PERTAMA: Satpam penjaga deadline (Mengecek setiap 30 detik)
    scheduler.add_job(kirim_pengingat_otomatis, trigger='interval', seconds=30)
    
    # 2. TUGAS KEDUA: Asisten pembuat laporan (Hanya menyala jam 07:00 pagi)
    scheduler.add_job(kirim_briefing_pagi, trigger='cron', hour=7, minute=0)
    
    # Mulai jalankan semua tugas di atas
    scheduler.start()
    yield
    scheduler.shutdown()
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
    
# ==========================================
# API: FITUR SELESAIKAN & HAPUS TUGAS
# ==========================================

@app.put("/api/tugas/{tugas_id}/selesai")
def selesaikan_tugas(tugas_id: int):
    with Session(engine) as session:
        tugas = session.get(Tugas, tugas_id)
        if not tugas:
            return {"error": "Tugas tidak ditemukan"}
        
        # Ubah status menjadi selesai
        tugas.is_selesai = True
        session.add(tugas)
        session.commit()
        return {"pesan": "Tugas berhasil diselesaikan"}

@app.delete("/api/tugas/{tugas_id}")
def hapus_tugas(tugas_id: int):
    with Session(engine) as session:
        tugas = session.get(Tugas, tugas_id)
        if not tugas:
            return {"error": "Tugas tidak ditemukan"}
        
        # Hapus tugas dari database
        session.delete(tugas)
        session.commit()
        return {"pesan": "Tugas berhasil dihapus"}
    
@app.put("/api/tugas/{tugas_id}")
def perbarui_tugas(tugas_id: int, tugas_baru: Tugas):
    with Session(engine) as session:
        tugas_lama = session.get(Tugas, tugas_id)
        if not tugas_lama:
            return {"error": "Tugas tidak ditemukan"}
        
        # LOGIKA CERDAS: Jika deadline diubah, reset status pengingat bot ke False
        if tugas_lama.deadline != tugas_baru.deadline:
            tugas_lama.is_diingatkan_h3 = False
            tugas_lama.is_diingatkan_h2 = False
            tugas_lama.is_diingatkan_h1 = False

        # Perbarui data lama dengan data yang baru diedit
        tugas_lama.mata_kuliah = tugas_baru.mata_kuliah
        tugas_lama.deskripsi = tugas_baru.deskripsi
        tugas_lama.prioritas = tugas_baru.prioritas
        tugas_lama.deadline = tugas_baru.deadline
        
        session.add(tugas_lama)
        session.commit()
        return {"pesan": "Tugas berhasil diperbarui"}