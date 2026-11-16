# DOL Numbering Service

Layanan microservice berbasis **FastAPI** untuk mengelola penomoran berbagai jenis dokumen (`SPPH`, `PO`, `PKS`, `SPK`) secara otomatis, sekuensial, dan **idempotent**. Service ini terintegrasi dengan database **PostgreSQL** dan dirancang untuk dikonsumsi oleh workflow otomatisasi **n8n**.

---

## 🚀 Fitur Utama

- **Multi-Dokumen**: Mendukung pembuatan nomor otomatis untuk jenis dokumen **SPPH**, **PO**, **PKS**, dan **SPK**.
- **Penomoran Sekuensial**: Menggunakan PostgreSQL _Sequence_ terpisah untuk setiap jenis dokumen guna memastikan nomor urut selalu unik.
- **Prinsip Idempotensi**: Mencegah pembuatan nomor ganda untuk kombinasi `id_lead`, `vendor_code`, dan `doc_type` yang sama saat dipanggil berulang kali.
- **Penyimpanan Log Otomatis**: Mencatat riwayat penomoran ke dalam tabel `document_file_logs` (dibuat otomatis jika belum tersedia).
- **Manajemen Konfigurasi**: Membaca kredensial database secara aman dari file `.env`.

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

---

## ⚙️ Cara Instalasi & Pengoperasian

### 1. Clone Repositori

```bash
git clone https://github.com/anggapriyadi/dol-numbering.git
cd dol-numbering
```

### 2. Buat & Aktifkan Virtual Environment (Opsional)

```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# Linux/MacOS:
source venv/bin/activate
```

### 3. Install Dependensi

```bash
pip install -r requirements.txt
```

### 4. Persiapan Database (PostgreSQL Sequences)

Tabel `document_file_logs` akan dibuat secara otomatis oleh aplikasi, namun Anda **wajib** membuat _sequence_ berikut di database PostgreSQL terlebih dahulu:

```sql
CREATE SEQUENCE IF NOT EXISTS number_spph_seq START 1;
CREATE SEQUENCE IF NOT EXISTS number_po_seq START 1;
CREATE SEQUENCE IF NOT EXISTS number_pks_seq START 1;
CREATE SEQUENCE IF NOT EXISTS number_spk_seq START 1;
```

### 5. Buat File `.env`

Buat file bernama `.env` di root direktori proyek dengan encoding **UTF-8**:

```env
DB_NAME=nama_database_anda
DB_USER=nama_user_database
DB_PASSWORD=password_database_anda
DB_HOST=nama_host_database
DB_PORT=5432
```

### 6. Jalankan Service

```bash
python main.py
```

Aplikasi akan berjalan di `http://127.0.0.1:8000`. Dokumentasi interaktif Swagger dapat diakses melalui `http://127.0.0`.

---

## 📡 API Endpoint

### Generate Nomor Dokumen

Membuat atau mengambil nomor resmi dokumen berdasarkan `id_lead`, `vendor_code`, dan `doc_type`.

- **URL:** `/generate-number`
- **Method:** `POST`
- **Headers:** `Content-Type: application/json`

#### Format Penomoran yang Didukung

| `doc_type` | Sequence PostgreSQL | Format Nomor Dokumen         | Contoh Output            |
| :--------- | :------------------ | :--------------------------- | :----------------------- |
| `SPPH`     | `number_spph_seq`   | `{NNN}/22/BIS-04/BUT/{YYYY}` | `001/22/BIS-04/BUT/2026` |
| `PO`       | `number_po_seq`     | `{NNN}/00/BIS-06/BUT/{YYYY}` | `001/00/BIS-06/BUT/2026` |
| `PKS`      | `number_pks_seq`    | `PKS/{YYYY}/{NNN}`           | `PKS/2026/001`           |
| `SPK`      | `number_spk_seq`    | `SPK/{YYYY}/{NNN}`           | `SPK/2026/001`           |

#### Request Body

```json
{
  "id_lead": "LEAD-12345",
  "nama_pekerjaan": "Pengadaan Server Utama",
  "vendor_code": "VND-001",
  "doc_type": "SPPH"
}
```

_(Catatan: Nilai `doc_type` bersifat case-insensitive dan menerima `"SPPH"`, `"PO"`, `"PKS"`, atau `"SPK"`)._

#### Response — Nomor Baru Berhasil Dibuat (`200 OK`)

```json
{
  "status": "generated",
  "doc_type": "SPPH",
  "nomor_dokumen": "001/22/BIS-04/BUT/2026"
}
```

#### Response — Data Sudah Ada / Idempotent (`200 OK`)

```json
{
  "status": "existing",
  "doc_type": "SPPH",
  "nomor_dokumen": "001/22/BIS-04/BUT/2026"
}
```

#### Response — Jenis Dokumen Tidak Valid (`400 Bad Request`)

```json
{
  "detail": "Invalid doc_type. Allowed: SPPH, PO, PKS, SPK"
}
```

---

## 🔄 Integrasi dengan n8n

1. Tambahkan node **HTTP Request** pada workflow n8n Anda.
2. Set **Method** ke `POST`.
3. Set **URL** ke `http://host.docker.internal:8000/generate-number` _(gunakan URL ini jika n8n berjalan di dalam Docker dan FastAPI berjalan di Local Host)_.
4. Pada bagian **Body Content Type**, pilih `JSON` dan masukkan payload sesuai format permintaan di atas dengan memetakan variabel dari node sebelumnya (`id_lead`, `nama_pekerjaan`, `vendor_code`, dan `doc_type`).
