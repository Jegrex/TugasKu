# TugasKu

# 📚 Sistem Pengingat Tugas Mahasiswa Baru (Telegram Bot + API)

Sistem ini dirancang sebagai solusi independen untuk membantu mahasiswa baru dalam melewati masa transisi dan adaptasi dengan ritme perkuliahan. Melalui pendekatan proaktif, sistem ini akan mengirimkan pengingat tugas secara otomatis guna meminimalisir risiko adanya tenggat waktu (*deadline*) yang terlewat.

## 🚀 Fitur Utama
- **Automated Scheduling (Proaktif):** Pengingat otomatis yang berjalan di latar belakang untuk mengirimkan daftar tugas aktif secara berkala kepada pengguna tanpa perlu dipicu manual.
- **Interaksi Bot Interaktif:** Mahasiswa dapat mengecek daftar tugas aktif (`/tugas`) dan menandai tugas yang sudah selesai (`/selesai <id>`) langsung dari aplikasi Telegram.
- **RESTful API Endpoint:** Backend berbasis FastAPI yang menyediakan jalur integrasi (CRUD) untuk penginputan data tugas di masa mendatang (misalnya via Web Dashboard Admin/Komti).
- **Arsitektur Data Aman:** Menggunakan SQLite dengan standardisasi pemisahan kredensial rahasia menggunakan variabel lingkungan (`.env`).

## 🛠️ Tech Stack
- **Language:** Python 3.13
- **Framework Backend:** FastAPI
- **Bot Library:** Aiogram (v3)
- **Database & ORM:** SQLite & SQLModel (SQLAlchemy)
- **Task Scheduler:** APScheduler (AsyncIOScheduler)

## 🔧 Cara Menjalankan Proyek Secara Lokal

1. Clone repositori ini:
   ```bash
   git clone <url-repositori-github-anda>
   cd <nama-folder-proyek>

2. Buat dan aktifkan Virtual Environment:
    ```bash
   python -m venv venv
   Windows:
   venv\Scripts\activate

3. Instal semua pustaka yang dibutuhkan:
    ```bash
   pip install -r requirements.txt

4. Buat file .env di folder utama dan lengkapi datanya:
    ```bash
   BOT_TOKEN=isi_token_bot_telegram_anda
   TARGET_USER_ID=isi_id_akun_telegram_anda

5. Jalankan server aplikasi:
    ```bash
   uvicorn main:app --reload
