import os
import random
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlmodel import Session, select
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

from database import engine
from models import Tugas, User

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# --- KOLEKSI ROASTING MAHASISWA (LEBIH BANYAK & PEDAS) ---
PESAN_H3 = [
    "👀 Cieee... Tugas *{matkul}* ({desk}) sisa 3 hari lagi. Prioritas: *{prio}*. Biasa, penganut agama SKS (Sistem Kebut Semalam) mah santai dulu, paniknya H-1 jam.",
    "🥱 H-3 nih buat *{matkul}* (Prioritas: *{prio}*). Udah ada niatan buka laptop belum, atau cuma sekadar buka Word terus ditinggal scroll TikTok?",
    "⏳ Tugas *{matkul}* sisa 3 hari. Jangan sampe numpuk! Ingat, beban hidup lu udah berat, jangan ditambahin beban tugas. (Level: *{prio}*)",
    "☕ Santai dulu ah, masih H-3 tugas *{matkul}*. Kata siapa? Kata setan yang mau ngajak lu ngulang matkul tahun depan! Buruan kerjain! (Level: *{prio}*)"
]

PESAN_H2 = [
    "🤨 Heh! Tugas *{matkul}* tinggal 2 HARI LAGI woy! Prioritas: *{prio}*. Lo tuh bukannya nggak ada waktu, tapi kebanyakan overthinking!",
    "⚠️ H-2 *{matkul}*! Kalo lo ngerjain sekarang lo masih bisa tidur nyenyak malemnya. Ayo kerjain, jangan jadi beban kelompok! (Prioritas: *{prio}*)",
    "🔥 Panas panas! Sisa 2 hari buat *{matkul}*. Ayo gerak, masa kalah sama rasa malas? Nanti nangis pas lihat nilai KHS. (Prioritas: *{prio}*)",
    "💻 Laptop lu udah nangis minta dibuka tuh buat ngerjain tugas *{matkul}* (H-2). Daripada nge-game terus, mending cicil tugasnya! (Prioritas: *{prio}*)"
]

PESAN_H1 = [
    "🚨 WADUH WADUH! Besok kumpul tugas *{matkul}* (Prioritas: *{prio}*)! Mampus, buruan kerjain woy, rebahan teroooos! 😭",
    "💀 WARNING! H-1 *{matkul}*! Kalo lo belum mulai juga, gue cuma bisa doain lo selamat dari amukan dosen. Siapin kopi, malam ini lo nggak tidur! (Prioritas: *{prio}*)",
    "⏰ TENG TENG TENG! Waktu rebahan habis! Besok deadline *{matkul}* (Level: *{prio}*). Kerjain sekarang atau siap-siap sungkem ke dosen minta perpanjangan!",
    "🚑 Gawat Darurat! H-1 tugas *{matkul}*. Mode panik: ON! Berhenti ngeliatin chat orang yang nggak bales-bales, tugas lo butuh perhatian lebih! (Prioritas: *{prio}*)"
]

# PERINTAH /start, /status, atau /id UNTUK CEK ID
@dp.message(Command("start", "status", "id"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    pesan = (
        f"👋 Woy! Gue Bot Pengingat Tugas lo yang paling julid.\n\n"
        f"🆔 **ID Telegram lo:** `{user_id}`\n\n"
        f"Copy tuh angka di atas, masukin ke form Pendaftaran di web. Biar gue bisa maki-maki elo kalo males ngerjain tugas!"
    )
    await message.answer(pesan, parse_mode="Markdown")

async def daily_recap_0700():
    with Session(engine) as session:
        users = session.exec(select(User)).all()
        for user in users:
            if not user.telegram_id: continue
            
            tugas_aktif = session.exec(select(Tugas).where(Tugas.owner_id == user.id, Tugas.is_selesai == False)).all()
            if not tugas_aktif: continue 
            
            pesan = f"🌞 **PAGI PEMALAS! BANGUN!** 🌞\n\nIni daftar beban hidup (tugas) yang belom lo kelarin:\n\n"
            for t in tugas_aktif:
                tgl = t.deadline.strftime('%d %b %H:%M')
                pesan += f"🔹 *{t.mata_kuliah}* - {t.deskripsi}\n   └ ⚠️ Prioritas: {t.prioritas} | ⏰ {tgl}\n\n"
            pesan += "Inget, penderitaan ini ga akan berakhir kalau ga lo kerjain! Semangat! 🔥"
            
            try: await bot.send_message(chat_id=user.telegram_id, text=pesan, parse_mode="Markdown")
            except: pass

async def cek_deadline_1930():
    with Session(engine) as session:
        sekarang_jkt = datetime.now(ZoneInfo("Asia/Jakarta"))
        tugas_aktif = session.exec(select(Tugas).where(Tugas.is_selesai == False)).all()
        
        for tugas in tugas_aktif:
            user = session.get(User, tugas.owner_id)
            if not user or not user.telegram_id: continue
            
            sisa_hari = (tugas.deadline.date() - sekarang_jkt.date()).days
            pesan = ""
            
            if sisa_hari == 3 and not tugas.is_diingatkan_h3:
                if tugas.prioritas == "Tinggi": pesan = random.choice(PESAN_H3).format(matkul=tugas.mata_kuliah, desk=tugas.deskripsi, prio=tugas.prioritas)
                tugas.is_diingatkan_h3 = True
            elif sisa_hari == 2 and not tugas.is_diingatkan_h2:
                if tugas.prioritas in ["Tinggi", "Sedang"]: pesan = random.choice(PESAN_H2).format(matkul=tugas.mata_kuliah, desk=tugas.deskripsi, prio=tugas.prioritas)
                tugas.is_diingatkan_h2 = True
            elif sisa_hari == 1 and not tugas.is_diingatkan_h1:
                pesan = random.choice(PESAN_H1).format(matkul=tugas.mata_kuliah, desk=tugas.deskripsi, prio=tugas.prioritas)
                tugas.is_diingatkan_h1 = True
            
            if pesan:
                try:
                    await bot.send_message(chat_id=user.telegram_id, text=pesan, parse_mode="Markdown")
                    session.add(tugas)
                    session.commit()
                except Exception as e: print(e)

async def start_bot():
    scheduler = AsyncIOScheduler(timezone=ZoneInfo("Asia/Jakarta"))
    scheduler.add_job(daily_recap_0700, CronTrigger(hour=8, minute=28))
    scheduler.add_job(cek_deadline_1930, CronTrigger(hour=1, minute=0))
    scheduler.start()
    print("🤖 Bot Roasting Aktif! Jadwal: 07:00 Pagi & 19:30 Malam (WIB).")
    await dp.start_polling(bot)