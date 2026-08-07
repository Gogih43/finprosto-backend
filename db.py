import sqlite3

# 1. Функция создания базы (создаст таблицы, если их нет)
def init_db():
    conn = sqlite3.connect('finprosto.db')
    c = conn.cursor()
    
    # Таблица со ставками (осталась как была)
    c.execute('''
        CREATE TABLE IF NOT EXISTS rates (
            bank_name TEXT PRIMARY KEY,
            rate REAL,
            badge TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # НОВАЯ ТАБЛИЦА: Статьи
    c.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id TEXT PRIMARY KEY,
            title TEXT,
            excerpt TEXT,
            category TEXT,
            readTime TEXT,
            date TEXT,
            imageGrad TEXT,
            content TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# 2. Функция сохранения ставки (осталась как была)
def save_rate(bank_name, rate, badge):
    if rate is None: return 
    conn = sqlite3.connect('finprosto.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO rates (bank_name, rate, badge, updated_at) 
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(bank_name) DO UPDATE SET 
        rate=excluded.rate, 
        badge=excluded.badge, 
        updated_at=CURRENT_TIMESTAMP
    ''', (bank_name, rate, badge))
    conn.commit()
    conn.close()

# 3. Функция чтения всех ставок (осталась как была)
def get_all_rates():
    conn = sqlite3.connect('finprosto.db')
    conn.row_factory = sqlite3.Row 
    c = conn.cursor()
    c.execute("SELECT * FROM rates")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# ==========================================
# НОВЫЕ ФУНКЦИИ ДЛЯ БАЗЫ ЗНАНИЙ (СЕО)
# ==========================================

# Загрузка одной статьи в базу (с защитой от дублей UPSERT)
def insert_article(data):
    conn = sqlite3.connect('finprosto.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO articles (id, title, excerpt, category, readTime, date, imageGrad, content)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
        title=excluded.title, excerpt=excluded.excerpt, category=excluded.category,
        readTime=excluded.readTime, date=excluded.date, imageGrad=excluded.imageGrad,
        content=excluded.content
    ''', (data['id'], data['title'], data['excerpt'], data['category'], data['readTime'], data['date'], data['imageGrad'], data['content']))
    conn.commit()
    conn.close()

# Чтение списка статей (БЕЗ текста, чтобы сайт летал)
def get_all_articles():
    conn = sqlite3.connect('finprosto.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    # Берем всё кроме content
    c.execute("SELECT id, title, excerpt, category, readTime, date, imageGrad FROM articles")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# Чтение одной конкретной статьи полностью
def get_article_by_id(article_id):
    conn = sqlite3.connect('finprosto.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None