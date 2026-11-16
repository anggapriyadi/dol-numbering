from fastapi import FastAPI, HTTPException
import psycopg2
from datetime import datetime
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import traceback

load_dotenv()

app = FastAPI(title="DOL Numbering Service")

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

# 1. Tambahkan doc_type ke payload agar n8n bisa mengirimkan jenis dokumen yang diminta
class DocumentPayload(BaseModel):
    id_lead: str
    nama_pekerjaan: str
    vendor_code: str
    doc_type: str  # Contoh nilai: "SPPH", "PO", "PKS", "SPK"

@app.post("/generate-number")
def generate_document_number(payload: DocumentPayload):
    conn = None
    cursor = None
    
    # Validasi jenis dokumen yang didukung
    doc_type = payload.doc_type.upper()
    if doc_type not in ["SPPH", "PO", "PKS", "SPK"]:
        raise HTTPException(status_code=400, detail="Invalid doc_type. Allowed: SPPH, PO, PKS, SPK")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # 2. Update Primary Key tabel log dengan menyertakan doc_type
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_file_logs (
                id_lead VARCHAR(50),
                vendor_code VARCHAR(50),
                doc_type VARCHAR(20),
                nomor_dokumen VARCHAR(100) UNIQUE,
                PRIMARY KEY (id_lead, vendor_code, doc_type)
            );
        """)
        conn.commit()

        # 3. Cek apakah dokumen untuk lead, vendor, dan jenis tersebut sudah pernah dibuat
        cursor.execute(
            "SELECT nomor_dokumen FROM document_file_logs WHERE id_lead = %s AND vendor_code = %s AND doc_type = %s;", 
            (payload.id_lead, payload.vendor_code, doc_type)
        )
        existing_number = cursor.fetchone()
        if existing_number:
            return {"status": "existing", "doc_type": doc_type, "nomor_dokumen": existing_number[0]}

        # 4. Tentukan sequence dan format nomor berdasarkan jenis dokumen
        tahun = datetime.now().strftime("%Y")
        
        if doc_type == "SPPH":
            cursor.execute("SELECT nextval('number_spph_seq');")
            next_id = cursor.fetchone()[0]
            nomor_resmi = f"{next_id:03d}/22/BIS-04/BUT/{tahun}"
            
        elif doc_type == "PO":
            cursor.execute("SELECT nextval('number_po_seq');") # Pastikan sequence ini sudah dibuat di PostgreSQL
            next_id = cursor.fetchone()[0]
            nomor_resmi = f"{next_id:03d}/00/BIS-06/BUT/{tahun}"
            
        elif doc_type == "PKS":
            cursor.execute("SELECT nextval('number_pks_seq');")
            next_id = cursor.fetchone()[0]
            nomor_resmi = f"PKS/{tahun}/{next_id:03d}"
            
        elif doc_type == "SPK":
            cursor.execute("SELECT nextval('number_spk_seq');")
            next_id = cursor.fetchone()[0]
            nomor_resmi = f"SPK/{tahun}/{next_id:03d}"

        # 5. Simpan log nomor dokumen baru ke database
        cursor.execute(
            "INSERT INTO document_file_logs (id_lead, vendor_code, doc_type, nomor_dokumen) VALUES (%s, %s, %s, %s);",
            (payload.id_lead, payload.vendor_code, doc_type, nomor_resmi)
        )
        conn.commit()

        return {"status": "generated", "doc_type": doc_type, "nomor_dokumen": nomor_resmi}

    except Exception as e:
        if conn:
            conn.rollback()
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
    uvicorn.run(app, host="127.0.0.1", port=8000)