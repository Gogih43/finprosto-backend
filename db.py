import sqlite3

# 1. Функция создания базы (создаст файл finprosto.db)
def init_db():
    conn = sqlite3.connect('finprosto.db')
    c = conn.cursor()
    # Создаем таблицу, если её еще нет
    c.execute('''
        CREATE TABLE IF NOT EXISTS rates (
            bank_name TEXT PRIMARY KEY,
            rate REAL,
            badge TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# 2. Функция сохранения ставки (Обновляет старую или создает новую)
def save_rate(bank_name, rate, badge):
    if rate is None: return # Если парсер сломался, не перезаписываем базу нулем
    
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

# 3. Функция чтения всех ставок (Для нашего API)
def get_all_rates():
    conn = sqlite3.connect('finprosto.db')
    conn.row_factory = sqlite3.Row # Чтобы ответ был красивым словарем, а не кортежем
    c = conn.cursor()
    c.execute("SELECT * FROM rates")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]