# DOL Numbering Service

Layanan microservice berbasis **FastAPI** untuk mengelola penomoran dokumen otomatis (Surat Permintaan Penawaran Harga / SPPH) secara sekuensial dan **idempotent**. Service ini terintegrasi dengan database **PostgreSQL** dan dikonsumsi oleh workflow otomatisasi **n8n**.

---

## 🚀 Fitur Utama

- **Penomoran Sekuensial**: Menggunakan PostgreSQL Sequence (`number_spph_seq`) untuk memastikan nomor urut selalu unik.
- **Prinsip Idempotensi**: Mencegah pembuat nomor ganda untuk `id_lead` yang sama saat dipanggil berulang kali.
- **Penyimpanan Log**: Mencatat riwayat penomoran ke dalam tabel `document_logs`.
- **Manajemen Konfigurasi**: Membaca variabel kredensial database dari file `.env`.

---

## 🛠️ Prasyarat & Teknologi

- **Python 3.10+**
- **PostgreSQL**
- **FastAPI** & **Uvicorn**
- **psycopg2-binary**
- **python-dotenv**

---

## 📂 Struktur Proyek

```text
dol-numbering/
├── .env              # Variabel lingkungan (kredensial DB)
├── main.py           # Skrip FastAPI utama
├── requirements.txt  # Daftar pustaka Python
└── README.md         # Dokumentasi proyek
```

⚙️ Cara Instalasi & Pengoperasian

1. Clone Repositori
   Bash
   git clone [https://github.com/anggapriyadi/dol-numbering.git](https://github.com/anggapriyadi/dol-numbering.git)
   cd dol-numbering
2. Buat & Aktifkan Virtual Environment (Opsional)
   Bash
   python -m venv venv

# Windows:

venv\Scripts\activate

# Linux/MacOS:

source venv/bin/activate

3. Install Dependensi
   Bash
   pip install -r requirements.txt

4. Buat File .env
   Buat file bernama .env di root direktori proyek dengan encoding UTF-8:
   DB_NAME=nama_database_anda
   DB_USER=nama_user_database
   DB_PASSWORD=password_database_anda
   DB_HOST=nama_host_database
   DB_PORT=port_database

5. Jalankan Service
   Bash
   python main.py
   Aplikasi akan berjalan di http://127.0.0.1:8000.

📡 API Endpoint
Generate Nomor SPPH
Membuat atau mengambil nomor surat SPPH berdasarkan ID Lead.

- URL: /generate-number-spph
- Method: POST
- Headers: Content-Type: application/json

Request Body
JSON
{
"id_lead": "LEAD-12345",
"nama_pekerjaan": "Pengadaan Server Utama"
}

Response (Nomor Baru Generated)
JSON
{
"status": "generated",
"nomor_spph": "001/22/ABC-04/ABC/2026"
}

Response (Jika Lead Sudah Ada - Idempotent)
JSON
{
"status": "existing",
"nomor_spph": "001/22/ABC-04/ABC/2026"
}

🔄 Integrasi dengan n8n

- Tambahkan node HTTP Request pada workflow n8n.

- Set Method ke POST.

- Set URL ke http://host.docker.internal:8000/generate-number-spph (jika n8n berjalan di Docker dan FastAPI di Local Host).

- Masukkan JSON Body sesuai dengan format permintaan di atas.
