from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db import init_db, get_all_rates

# При старте сервера убеждаемся, что база создана
init_db()

app = FastAPI(title="FINПРОСТО API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/get_cbr_rate")
def get_cbr_rate():
    # Читаем базу данных
    rates = get_all_rates()
    # Ищем ставку ЦБ
    for row in rates:
        if row["bank_name"] == "ЦБ РФ":
            return {"status": "success", "cbr_rate": row["rate"]}
    return {"status": "error", "message": "Ставка ЦБ не найдена в базе"}

@app.get("/api/get_market_data")
def get_market_data():
    rates = get_all_rates()
    
    # Фильтруем: убираем ЦБ РФ из списка коммерческих банков
    banks_only = [
        {"name": r["bank_name"], "rate": r["rate"], "badge": r["badge"]}
        for r in rates if r["bank_name"] != "ЦБ РФ"
    ]
    
    return {
        "status": "success",
        "data": {"banks": banks_only}
    }