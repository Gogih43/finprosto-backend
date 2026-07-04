import sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = "GOGIH_SUPER_SECRET_2026"

def get_db_connection():
    conn = sqlite3.connect('finprosto.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bank_name TEXT NOT NULL,
            rate REAL NOT NULL,
            badge TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
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
        raise HTTPException(status_code=403, detail="Неверный пароль!")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM rates")
        for item in payload.rates:
            cursor.execute(
                "INSERT INTO rates (bank_name, rate, badge) VALUES (?, ?, ?)",
                (item.name, item.rate, item.badge)
            )
        conn.commit()
        conn.close()
        return {"status": "success", "message": "База обновлена!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/get_market_data")
def get_market_data():
    fallback_banks = [
        {"name": "Альфа-Банк", "rate": 17.4, "badge": "Лучшее решение"},
        {"name": "СберБанк", "rate": 17.9, "badge": "+ 21 000 ₽ переплаты"},
        {"name": "ВТБ", "rate": 15.9, "badge": "Обязательная страховка"},
        {"name": "Т-Банк", "rate": 14.9, "badge": "Скрытые комиссии"}
    ]
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT bank_name as name, rate, badge FROM rates WHERE bank_name != 'ЦБ РФ' GROUP BY bank_name")
        banks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        if len(banks) == 0:
            banks = fallback_banks
        else:
            banks.sort(key=lambda x: x["rate"])
        return {"status": "success", "data": {"banks": banks}}
    except Exception:
        return {"status": "success", "data": {"banks": fallback_banks}}

@app.get("/api/get_cbr_rate")
def get_cbr_rate():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT rate FROM rates WHERE bank_name = 'ЦБ РФ' ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        if row: return {"status": "success", "cbr_rate": row["rate"]}
        return {"status": "success", "cbr_rate": 14.25}
    except Exception:
        return {"status": "success", "cbr_rate": 14.25}

# 🔥 ИСПРАВЛЕНО: ТЕПЕРЬ ОТДАЕМ И ИМЯ БАНКА ТОЖЕ 🔥
@app.get("/api/get_best_offer")
def get_best_offer():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT bank_name, rate FROM rates WHERE bank_name != 'ЦБ РФ' ORDER BY rate ASC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        if row: return {"status": "success", "bank_name": row["bank_name"], "real_rate": row["rate"]}
        return {"status": "success", "bank_name": "Альфа-Банк", "real_rate": 17.4}
    except Exception:
        return {"status": "success", "bank_name": "Альфа-Банк", "real_rate": 17.4}