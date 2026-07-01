# 🎓 Task Manager Mahasiswa (Terintegrasi Bot Telegram)

Aplikasi manajemen tugas perkuliahan berbasis web modern yang dirancang untuk membantu mahasiswa mengorganisasi aktivitas akademik secara efektif. Sistem ini mengintegrasikan *dashboard* interaktif dengan asisten virtual Bot Telegram proaktif yang berfungsi sebagai pengingat tenggat waktu (*deadline*) dan penasihat harian.

---

## ✨ Fitur Utama

### 1. Dashboard Web Interaktif & Responsif
* **Tata Letak Grid Adaptif:** UI yang dirancang menggunakan Tailwind CSS, memastikan kenyamanan akses baik melalui perangkat *mobile* (HP) maupun desktop (Laptop).
* **Smart Filtering & Real-Time Search:** Pencarian dinamis berdasarkan kata kunci mata kuliah atau deskripsi tugas, dilengkapi filter instan berdasarkan status tugas (Aktif/Selesai) tanpa memuat ulang halaman (*Single Page Application experience*).
* **Indikator Progres Visual:** *Progress bar* dinamis yang menghitung rasio penyelesaian tugas secara otomatis untuk memberikan motivasi visual.
* **Sistem Manajemen Data Modern:** Didukung oleh komponen pop-up interaktif dari SweetAlert2 untuk konfirmasi penambahan, penyelesaian, dan penghapusan data secara elegan.

### 2. Otomasi Asisten Virtual Bot Telegram (Dua Arah)
* **Penjaga Tenggat Waktu (Satpam Deadline):** Pemantauan otomatis secara *real-time* untuk mendeteksi tugas prioritas tinggi dan mengirimkan alarm pengingat bertahap pada H-3, H-2, dan H-1 sebelum waktu habis.
* **Daily Morning Briefing:** Pesan rekapitulasi otomatis setiap pukul 07:00 pagi yang menjabarkan seluruh daftar tugas aktif, statistik tingkat urgensi, serta fokus utama hari itu.
* **Sistem Kontrol Jarak Jauh (2-Way Interaction):** Kemampuan bot untuk merespons perintah teks (seperti `/tugas`) dan menyediakan *Inline Keyboard* (tombol fisik di dalam chat) sehingga pengguna dapat menandai tugas selesai langsung dari aplikasi Telegram.

---

## 🛠️ Arsitektur & Teknologi

Aplikasi ini menggunakan pendekatan arsitektur modern yang memisahkan tanggung jawab antara penyimpanan data, logika bisnis, dan penyajian antarmuka:

* **Backend (Logika Bisnis):** [FastAPI](https://fastapi.tiangolo.com/) (Python) – Dipilih karena performanya yang tinggi, asinkron, dan efisiensi dalam pembuatan REST API.
* **Penyimpanan Data (Database):** [SQLModel](https://sqlmodel.tiangolo.com/) & [PostgreSQL](https://www.postgresql.org/) (Hosted via Neon.tech) – Menjamin relasi data yang kuat, integritas identitas (*auto-increment id*), dan performa *query* yang stabil.
* **Penjadwalan Otomatis (Automation):** [APScheduler](https://apscheduler.readthedocs.io/) – Mengelola eksekusi tugas latar belakang secara paralel untuk fungsi *interval* (30 detik) dan *cron* (jam 07:00 pagi).
* **Antarmuka Pengguna (Frontend):** HTML5 murni dikombinasikan dengan [Tailwind CSS](https://tailwindcss.com/) (Styling) dan JavaScript murni (Fetch API & DOM Manipulation).

---

## 🤖 Transparansi & Metodologi Pengembangan (AI-Assisted Development)

Proyek ini dibangun menggunakan metode kolaborasi modern antara **Pengembang Manusia (Human Developer)** dan **Kecerdasan Buatan (Generative AI)**. Pendekatan ini diterapkan untuk mempercepat siklus pengerjaan, memastikan keamanan kode, dan menerapkan standar industri pada aplikasi skala kecil.

Keterlibatan AI dalam proyek ini mencakup aspek-aspek berikut:

1.  **Perancangan Arsitektur Sistem:** AI digunakan sebagai mitra diskusi untuk menentukan struktur tabel database (*Multi-Tenancy*), relasi antar-entitas, serta alur kerja asinkron antara FastAPI dan ekosistem Telegram Bot API.
2.  **Penulisan & Optimasi Kode:** Pembuatan struktur dasar komponen API, penanganan manajemen waktu (penerjemahan format ISO UTC ke zona waktu lokal), serta implementasi fungsi penutupan koneksi (*lifespan manager*).
3.  **Refactoring UI/UX:** Transformasi tampilan antarmuka dari HTML standar menjadi grid responsif berbasis Tailwind CSS, serta penggantian fungsi notifikasi kaku (`alert()`) menjadi komponen interaktif SweetAlert2.
4.  **Uji Coba & Debugging:** Penanganan kendala teknis seperti konversi penanda baris file (LF/CRLF), penanganan eror pembacaan skrip, dan validasi data saat pembaruan status data.

**Pernyataan Kontrol:** Meskipun AI memberikan rekomendasi kode dan efisiensi logika, seluruh kendali strategis, validasi keamanan data, penyelarasan fungsi dengan kebutuhan riil mahasiswa, serta keputusan akhir arsitektur tetap sepenuhnya dipegang dan dieksekusi oleh Pengembang Manusia.

---

## 📈 Rencana Pengembangan Selanjutnya (Roadmap)

Ke depan, sistem ini dipersiapkan untuk bertransisi dari aplikasi lokal menjadi aplikasi publik berskala luas (*Scalable Multi-User Cloud App*) dengan rencana penambahan fitur berikut:

- [ ] **Sistem Autentikasi Pengguna:** Implementasi halaman *Login* dan *Register* menggunakan enkripsi kata sandi (Password Hashing) dan JWT Token.
- [ ] **Isolasi Data (Multi-Tenant Database):** Pemisahan hak akses data menggunakan kunci `user_id` agar banyak pengguna dapat menggunakan satu aplikasi tanpa kebocoran data antar-pengguna.
- [ ] **Quick Add Telegram:** Fitur penambahan tugas secara instan langsung melalui ketikan pesan di ruang obrolan Telegram menggunakan parameter teks terstruktur.
- [ ] **Cloud Deployment:** Migrasi server ke layanan *always-on* (seperti Render/Railway) untuk memastikan operasional penuh 24/7 tanpa bergantung pada perangkat lokal.
