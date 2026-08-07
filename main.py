from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from db import init_db, get_all_rates, get_all_articles, get_article_by_id

# При старте сервера убеждаемся, что база и новые таблицы созданы
init_db()

app = FastAPI(title="FINПРОСТО API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === СТАРЫЕ ЭНДПОИНТЫ ===

@app.get("/api/get_cbr_rate")
def get_cbr_rate():
    rates = get_all_rates()
    for row in rates:
        if row["bank_name"] == "ЦБ РФ":
            return {"status": "success", "cbr_rate": row["rate"]}
    return {"status": "error", "message": "Ставка ЦБ не найдена в базе"}

@app.get("/api/get_market_data")
def get_market_data():
    rates = get_all_rates()
    banks_only = [
        {"name": r["bank_name"], "rate": r["rate"], "badge": r["badge"]}
        for r in rates if r["bank_name"] != "ЦБ РФ"
    ]
    return {
        "status": "success",
        "data": {"banks": banks_only}
    }

# === НОВЫЕ ЭНДПОИНТЫ ДЛЯ СТАТЕЙ (SEO) ===

@app.get("/api/articles")
def get_articles_list():
    """Отдает список всех статей для Главной страницы"""
    articles = get_all_articles()
    return {
        "status": "success",
        "data": articles
    }

@app.get("/api/articles/{article_id}")
def get_single_article(article_id: str):
    """Отдает полный текст конкретной статьи"""
    article = get_article_by_id(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Статья не найдена")
    
    return {
        "status": "success",
        "data": article
    }