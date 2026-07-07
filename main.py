import sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

SECRET_KEY = "GOGIH_SUPER_SECRET_2026"

def get_db_connection():
    conn = sqlite3.connect('finprosto.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    # Добавлен UNIQUE для bank_name, чтобы база не дублировала, а обновляла банки
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            bank_name TEXT UNIQUE NOT NULL, 
            rate REAL NOT NULL, 
            badge TEXT
        )
    ''')
    conn.commit()
    return conn

class RateItem(BaseModel): 
    name: str
    rate: float
    badge: str

class UpdatePayload(BaseModel): 
    secret_key: str
    rates: List[RateItem]

@app.post("/api/update_rates")
def update_rates(payload: UpdatePayload):
    if payload.secret_key != SECRET_KEY: 
        raise HTTPException(status_code=403)
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Обновляем те банки, что прислал шпион. Остальные не трогаем (сохранят старую ставку).
        for item in payload.rates:
            if item.rate <= 0:
                continue
            
            cursor.execute("""
                INSERT INTO rates (bank_name, rate, badge) 
                VALUES (?, ?, ?)
                ON CONFLICT(bank_name) DO UPDATE SET 
                rate=excluded.rate, 
                badge=excluded.badge
            """, (item.name, item.rate, item.badge))
            
        conn.commit()
        conn.close()
        return {"status": "success", "updated_banks": len(payload.rates)}
    except Exception as e: 
        print(f"DB Error: {e}")
        return {"status": "error"}

@app.get("/api/get_market_data")
def get_market_data():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT bank_name as name, rate, badge FROM rates WHERE bank_name != 'ЦБ РФ' GROUP BY bank_name")
        banks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        if banks: 
            banks.sort(key=lambda x: x["rate"])
        return {"status": "success", "data": {"banks": banks}}
    except Exception: 
        return {"status": "error"}

@app.get("/api/get_cbr_rate")
def get_cbr_rate():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT rate FROM rates WHERE bank_name = 'ЦБ РФ' ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        if row: 
            return {"status": "success", "cbr_rate": row["rate"]}
        return {"status": "success", "cbr_rate": 14.25}
    except Exception: 
        return {"status": "success", "cbr_rate": 14.25}

@app.get("/api/get_best_offer")
def get_best_offer():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT bank_name, rate FROM rates WHERE bank_name != 'ЦБ РФ' ORDER BY rate ASC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        if row: 
            return {"status": "success", "bank_name": row["bank_name"], "real_rate": row["rate"]}
        return {"status": "success", "bank_name": "Альфа-Банк", "real_rate": 17.4}
    except Exception: 
        return {"status": "success"}