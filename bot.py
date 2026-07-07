import os
import random
import pytz
from datetime import datetime, timedelta
from sqlmodel import Session, select
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv
from aiogram import F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlmodel import select, Session
from database import engine
from models import User, Tugas
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
from database import engine
from models import Tugas, User
from aiogram.types import WebAppInfo
from aiogram.types import BotCommand


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

@dp.message(Command("tugas"))
async def cmd_tugas(message: types.Message):
    telegram_id = str(message.from_user.id)
    
    with Session(engine) as session:
        # Cari user berdasarkan telegram_id
        user = session.exec(select(User).where(User.telegram_id == telegram_id)).first()
        
        if not user:
            await message.reply("Hadeh, lu siapa? Daftar dulu sana di web, masukin Telegram ID lu yang ini: " f"`{telegram_id}`")
            return
            
        # Cari tugas yang belum selesai
        tugas_aktif = session.exec(
            select(Tugas).where(Tugas.owner_id == user.id, Tugas.is_selesai == False)
        ).all()
        
        if not tugas_aktif:
            await message.reply("Wah tumben lu rajin! Udah nggak ada tugas yang numpuk. Bebas rebahan! 🛌✨")
            return
            
        await message.reply(f"Woy, masih ada {len(tugas_aktif)} tugas yang belum lu kerjain! Nih listnya:")
        
        # Kirim tugas satu per satu dengan tombol interaktif
        # Kirim tugas satu per satu dengan tombol interaktif
        for t in tugas_aktif:
            builder = InlineKeyboardBuilder()
            
            # Tambah 3 Tombol
            builder.button(text="✅ Selesai", callback_data=f"selesai_{t.id}")
            builder.button(text="⏰ +1 Hari", callback_data=f"tunda_{t.id}")
            builder.button(text="🗑️ Hapus", callback_data=f"hapus_{t.id}")
            
            # Susun posisinya: 1 tombol di baris pertama, 2 tombol di baris kedua
            builder.adjust(1, 2)
            
            teks_tugas = (
                f"📚 **{t.mata_kuliah}**\n"
                f"📝 {t.deskripsi}\n"
                f"⏰ Deadline: {t.deadline.strftime('%d %b %Y %H:%M')}\n"
                f"🔥 Prioritas: {t.prioritas}"
            )
            
            await message.answer(teks_tugas, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("selesai_"))
async def proses_selesai(callback: types.CallbackQuery):
    tugas_id = int(callback.data.split("_")[1])
    
    with Session(engine) as session:
        tugas = session.get(Tugas, tugas_id)
        
        if not tugas or tugas.is_selesai:
            await callback.answer("Tugas ini udah nggak aktif!", show_alert=True)
            return
            
        # --- LOGIKA PENGECEKAN KETERLAMBATAN ---
        sekarang = datetime.now() # Mengambil waktu saat tombol dipencet
        
        if sekarang > tugas.deadline:
            # JIKA TELAT
            roasting_telat = [
                "Baru kelar SEKARANG?! Udah basi woy! Keburu pensiun dosennya! 😡",
                "Telat! Kalau ini bom, lu udah hancur berkeping-keping dari kemarin. 💥",
                "Mending gausah dikerjain sekalian kalau telat begini. Eh canda, bagus deh seenggaknya kelar. 😒"
            ]
            respon = random.choice(roasting_telat)
            status_teks = "✅ **SELESAI (TAPI TELAT!)** 🐌"
        else:
            # JIKA TEPAT WAKTU
            pujian_awal = [
                "Tumben kelar sebelum deadline. Kesambet jin rajin lu? 👻",
                "Wah, keajaiban dunia! Tugas kelar tepat waktu. Pertahankan! ✨",
                "Bagus. Akhirnya lu bisa main game tanpa beban dosa. 🎮"
            ]
            respon = random.choice(pujian_awal)
            status_teks = "✅ **SELESAI TEPAT WAKTU!** 🏆"

        # Tandai selesai di database
        tugas.is_selesai = True
        session.add(tugas)
        session.commit()
        
        # Edit pesan Telegram
        teks_baru = (
            f"~~{tugas.mata_kuliah}: {tugas.deskripsi}~~\n"
            f"{status_teks}\n\n"
            f"🤖 *Bot:* {respon}"
        )
        await callback.message.edit_text(teks_baru, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("tunda_"))
async def proses_tunda(callback: types.CallbackQuery):
    tugas_id = int(callback.data.split("_")[1])
    
    with Session(engine) as session:
        tugas = session.get(Tugas, tugas_id)
        if not tugas:
            await callback.answer("Tugas tidak ditemukan!", show_alert=True)
            return
            
        # Tambah deadline 1 hari (24 jam)
        tugas.deadline = tugas.deadline + timedelta(days=1)
        session.add(tugas)
        session.commit()
        
        await callback.answer("Deadline berhasil diundur 1 hari! Dasar tukang nunda!", show_alert=True)
        
        # Perbarui teks di layar
        teks_baru = (
            f"📚 **{tugas.mata_kuliah}**\n"
            f"📝 {tugas.deskripsi}\n"
            f"⏰ Deadline Baru: {tugas.deadline.strftime('%d %b %Y %H:%M')} (Diundur)\n"
            f"🔥 Prioritas: {tugas.prioritas}\n\n"
            f"🤖 *Bot:* Dasar kang nunda! Awas aja besok masih belom kelar!"
        )
        await callback.message.edit_text(teks_baru, reply_markup=callback.message.reply_markup, parse_mode="Markdown")

# Penangkap tombol HAPUS
@dp.callback_query(F.data.startswith("hapus_"))
async def proses_hapus(callback: types.CallbackQuery):
    tugas_id = int(callback.data.split("_")[1])
    
    with Session(engine) as session:
        tugas = session.get(Tugas, tugas_id)
        if tugas:
            session.delete(tugas)
            session.commit()
            
        # Hapus pesan dari layar Telegram sepenuhnya
        await callback.message.delete()
        await callback.answer("Tugas berhasil dibakar (dihapus)! 🔥", show_alert=True)


    
# PERINTAH /start, /status, atau /id UNTUK CEK ID
@dp.message(Command("start", "status", "id"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    pesan = (
        f"👋 Woy! Gue Bot Pengingat Tugas lo yang paling keren.\n\n"
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

# --- SISTEM INPUT TUGAS DARI TELEGRAM (FSM) ---

class FormTugas(StatesGroup):
    matkul = State()
    deskripsi = State()
    deadline = State()
    prioritas = State()

@dp.message(Command("tambah"))
async def cmd_tambah(message: types.Message, state: FSMContext):
    telegram_id = str(message.from_user.id)
    with Session(engine) as session:
        user = session.exec(select(User).where(User.telegram_id == telegram_id)).first()
        if not user:
            await message.reply("Lu siapa? Daftar/Login dulu di web, terus masukin ID Telegram lu yang ini: " f"`{telegram_id}`", parse_mode="Markdown")
            return
            
    await message.reply("Mau nambah tugas? Tumben rajin. \nApa nama **Mata Kuliah**-nya?", parse_mode="Markdown")
    await state.set_state(FormTugas.matkul)
    
@dp.message(FormTugas.matkul)
async def proses_matkul(message: types.Message, state: FSMContext):
    await state.update_data(matkul=message.text)
    await message.reply("Sip. Terus, ketik **Deskripsi** atau detail tugasnya:")
    await state.set_state(FormTugas.deskripsi)
    
@dp.message(FormTugas.deskripsi)
async def proses_deskripsi(message: types.Message, state: FSMContext):
    await state.update_data(deskripsi=message.text)
    await message.reply(
        "Catat. Kapan **Deadline**-nya?\n"
        "Tulis pakai format begini woy: `YYYY-MM-DD HH:MM`\n"
        "Contoh: `2024-12-30 23:59`", 
        parse_mode="Markdown"
    )
    await state.set_state(FormTugas.deadline)
    
@dp.message(FormTugas.deadline)
async def proses_deadline(message: types.Message, state: FSMContext):
    try:
        # Cek apakah format waktunya benar
        deadline_date = datetime.strptime(message.text, "%Y-%m-%d %H:%M")
        await state.update_data(deadline=deadline_date)
        
        # Bikin tombol untuk Prioritas
        builder = InlineKeyboardBuilder()
        builder.button(text="🔥 Tinggi", callback_data="pri_Tinggi")
        builder.button(text="⚠️ Sedang", callback_data="pri_Sedang")
        builder.button(text="🟢 Rendah", callback_data="pri_Rendah")
        builder.adjust(3)
        
        await message.reply("Terakhir nih, pilih **Prioritas** tugasnya:", reply_markup=builder.as_markup(), parse_mode="Markdown")
        await state.set_state(FormTugas.prioritas)
    except ValueError:
        await message.reply("Format waktu lu salah! Yang bener aja dong. Ulangi pakai format: `YYYY-MM-DD HH:MM`", parse_mode="Markdown")

@dp.callback_query(F.data.startswith("pri_"), FormTugas.prioritas)
async def proses_prioritas(callback: types.CallbackQuery, state: FSMContext):
    prioritas = callback.data.split("_")[1]
    data = await state.get_data()
    telegram_id = str(callback.from_user.id)
    
    with Session(engine) as session:
        user = session.exec(select(User).where(User.telegram_id == telegram_id)).first()
        tugas_baru = Tugas(
            mata_kuliah=data['matkul'], deskripsi=data['deskripsi'],
            deadline=data['deadline'], prioritas=prioritas,
            is_selesai=False, owner_id=user.id
        )
        session.add(tugas_baru)
        session.commit()
        
    await callback.message.edit_text(f"✅ Mantap! Tugas **{data['matkul']}** sukses gue simpan ke database.\nJangan lupa dikerjain, awas aja kalau telat!", parse_mode="Markdown")
    await state.clear()

@dp.message(Command("buka"))
async def cmd_buka_app(message: types.Message):
    builder = InlineKeyboardBuilder()
    # GANTI URL di bawah dengan URL Railway Anda! (Wajib HTTPS)
    builder.button(text="🚀 Buka Task Manager", web_app=WebAppInfo(url="https://tugasku-production.up.railway.app"))

    await message.reply("Males ngetik chat? Langsung buka aplikasinya di sini aja bos:", reply_markup=builder.as_markup())

# ==========================================
# FITUR BARU: COMMAND BOT PLENGER (AMAN, TIDAK MENGHAPUS FITUR LAMA)
# ==========================================

from datetime import datetime, timedelta

@dp.message(Command("besok"))
async def cmd_besok(message: types.Message):
    telegram_id = str(message.from_user.id)
    with Session(engine) as session:
        user = session.exec(select(User).where(User.telegram_id == telegram_id)).first()
        if not user:
            await message.reply("Lu siapa? Daftar dulu sana, dasar plenger! ID lu: " f"`{telegram_id}`", parse_mode="Markdown")
            return
        
        # Cari deadline 24 jam ke depan
        besok = datetime.now() + timedelta(hours=24)
        tugas_mepet = session.exec(
            select(Tugas).where(
                Tugas.owner_id == user.id, 
                Tugas.is_selesai == False,
                Tugas.deadline <= besok
            )
        ).all()
        
        if not tugas_mepet:
            await message.reply("Aman bos! Nggak ada deadline maut dalam 24 jam ke depan. Bisa rebahan sambil ngopi. ☕")
            return
            
        pesan = f"🚨 **WOY PLENGER! ADA {len(tugas_mepet)} TUGAS MEPET 24 JAM!** 🚨\nJangan cengengesan, buruan kerjain:\n\n"
        for t in tugas_mepet:
            pesan += f"📚 **{t.mata_kuliah}**\n⏰ {t.deadline.strftime('%d %b %H:%M')}\n📝 {t.deskripsi}\n\n"
        
        await message.reply(pesan, parse_mode="Markdown")


@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    telegram_id = str(message.from_user.id)
    with Session(engine) as session:
        user = session.exec(select(User).where(User.telegram_id == telegram_id)).first()
        if not user: return
        
        selesai = len(session.exec(select(Tugas).where(Tugas.owner_id == user.id, Tugas.is_selesai == True)).all())
        aktif = len(session.exec(select(Tugas).where(Tugas.owner_id == user.id, Tugas.is_selesai == False)).all())
        
        pesan = (
            "📊 **RAPOT KEMALASAN LU:**\n\n"
            f"✅ Udah Kelar: {selesai} Tugas\n"
            f"⚠️ Nunggak: {aktif} Tugas\n\n"
        )
        
        # Reaksi bot tergantung rasio kelar vs nunggak
        if aktif > selesai:
            pesan += "Banyakan yang nunggak daripada yang kelar. Plenger emang lu, niat kuliah gak sih? 🗿"
        elif aktif == 0 and selesai > 0:
            pesan += "Wah nol tunggakan? Kesambet jin rajin lu hari ini? Lanjutin yak! 🔥"
        else:
            pesan += "Lumayan lah, seenggaknya ada progres. Jangan cepet puas lu!"
            
        await message.reply(pesan, parse_mode="Markdown")


@dp.message(Command("roasting"))
async def cmd_roasting(message: types.Message):
    telegram_id = str(message.from_user.id)
    with Session(engine) as session:
        user = session.exec(select(User).where(User.telegram_id == telegram_id)).first()
        if not user: return
        
        aktif = session.exec(select(Tugas).where(Tugas.owner_id == user.id, Tugas.is_selesai == False)).all()
        
        if len(aktif) == 0:
            await message.reply("Mau gue roasting? Tugas lu aja udah kelar semua. Gue yang keliatan plenger ntar kalau ngomel-ngomel gak jelas. Udah sana main game! 🎮")
        elif len(aktif) < 3:
            await message.reply(f"Ada {len(aktif)} tugas doang mah kecil. Gitu aja sok-sokan minta di-roasting. Kerjain sekarang, 10 menit juga kelar kocak! 🥱")
        else:
            await message.reply(f"Muka lu kek orang plenger, tugas numpuk {len(aktif)} biji malah mainan bot! Lu kira dosen lu bakal ngasih nilai A jalur kasihan? Buka laptop sana, kerjain! Malah senyum-senyum lagi baca ini. 😡")

async def start_bot():
    bot_commands = [
        BotCommand(command="/start", description="🏠 Menu Utama & Buka App"),
        BotCommand(command="/status", description="🆔 Cek ID Telegram lu"),
        BotCommand(command="/tambah", description="✏️ Input Tugas langsung dari sini"),
        BotCommand(command="/tugas", description="📋 Cek semua tugas lu"),
        BotCommand(command="/besok", description="🚨 Cek deadline maut (24 Jam)"),
        BotCommand(command="/stats", description="📊 Liat rapot kemalasan lu"),
        BotCommand(command="/roasting", description="🔥 Uji mental lu di sini")
    ]
    await bot.set_my_commands(bot_commands)
    # 1. Set zona waktu Jakarta menggunakan pytz
    wib = pytz.timezone('Asia/Jakarta')
    scheduler = AsyncIOScheduler(timezone=wib)
    
    # 2. KEMBALIKAN KE JAM ASLI (Tidak perlu diakali lagi!)
    # Karena sudah pakai WIB, tulis jam 7 untuk jam 7 pagi, dan jam 19 untuk jam 7 malam.
    scheduler.add_job(daily_recap_0700, CronTrigger(hour=7, minute=0))
    scheduler.add_job(cek_deadline_1930, CronTrigger(hour=19, minute=30))
    
    scheduler.start()
    print("🤖 Bot Roasting Aktif! Jadwal: 07:00 Pagi & 19:30 Malam (WIB).")
    
    await dp.start_polling(bot)