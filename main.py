from fastapi import FastAPI, HTTPException
import psycopg2
from datetime import datetime
from pydantic import BaseModel

import os
from dotenv import load_dotenv

# Memuat variabel dari file .env
load_dotenv()

app = FastAPI(title="DOL Numbering Service")

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}


# Skema request data dari n8n
class ProjectPayload(BaseModel):
    id_lead: str
    nama_pekerjaan: str

import traceback

@app.post("/generate-number-spph") # Diubah ke POST agar bisa menerima body JSON dari n8n
def generate_number(payload: ProjectPayload):
    # conn = psycopg2.connect(**DB_CONFIG)
    conn = None
    # cursor = conn.cursor()
    cursor = None
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # 1. Buat tabel log otomatis jika belum ada (Bulan 2 Fondasi)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_logs (
                id_lead VARCHAR(50) PRIMARY KEY,
                nomor_spph VARCHAR(100) UNIQUE
            );
        """)
        conn.commit()

        # 2. Cek apakah id_lead ini sudah pernah minta nomor surat (Idempotent Check)
        cursor.execute("SELECT nomor_spph FROM document_logs WHERE id_lead = %s;", (payload.id_lead,))
        existing_number = cursor.fetchone()
        if existing_number:
            return {"status": "existing", "nomor_spph": existing_number[0]}

        # 3. Jika proyek baru, ambil nomor urut dari PostgreSQL Sequence
        cursor.execute("SELECT nextval('number_spph_seq');")
        next_id = cursor.fetchone()[0]

        tahun = datetime.now().strftime("%Y")
        nomor_resmi = f"{next_id:03d}/22/BIS-04/BUT/{tahun}"

        # 4. Amankan nomor tersebut ke tabel log sebelum dikirim ke n8n
        cursor.execute(
            "INSERT INTO document_logs (id_lead, nomor_spph) VALUES (%s, %s);",
            (payload.id_lead, nomor_resmi)
        )
        conn.commit()

        return {"status": "generated", "nomor_spph": nomor_resmi}

    except Exception as e:
        if conn:
            conn.rollback()
        # cetak error ke terminal
        print("=== DETAIL ERROR ===")
        traceback.print_exc()
        print("====================")
        raise HTTPException(status_code=500, detail=f"Database Error: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    import uvicorn
    # Mengubah host ke 0.0.0.0 dan mengunci port 8000 agar tidak bentrok dengan Render Service
    uvicorn.run(app, host="127.0.0.1", port=8000)
