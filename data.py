import sqlite3
import os.path

def init_db():
    conn = sqlite3.connect("budget.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS categories
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, fixed REAL, min REAL, weight REAL, active INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS goals
                 (name TEXT, amount REAL, term INTEGER)''')
    conn.commit()
    conn.close()

def load_categories():
    init_db()
    conn = sqlite3.connect("budget.db")
    c = conn.cursor()
    c.execute("SELECT name, fixed, min, weight, active FROM categories")
    categories = [{"name": row[0], "fixed": row[1], "min": row[2], "weight": row[3], "active": row[4]} for row in c.fetchall()]
    conn.close()
    if not categories:
        categories = [
            {"name": "Аренда жилья / ипотека", "fixed": 30000.0, "min": 30000.0, "weight": 5.0, "active": 1},
            {"name": "Коммунальные услуги", "fixed": 5000.0, "min": 5000.0, "weight": 5.0, "active": 1},
            {"name": "Интернет и мобильная связь", "fixed": 1000.0, "min": 1000.0, "weight": 4.0, "active": 1},
            {"name": "Налоги и страховки", "fixed": 2000.0, "min": 2000.0, "weight": 4.0, "active": 1},
            {"name": "Продукты", "fixed": None, "min": 15000.0, "weight": 7.0, "active": 1},
            {"name": "Кафе и рестораны", "fixed": None, "min": 2000.0, "weight": 3.0, "active": 1},
            {"name": "Проезд", "fixed": None, "min": 3000.0, "weight": 5.0, "active": 1},
            {"name": "Обслуживание и ремонт", "fixed": None, "min": 0.0, "weight": 5.0, "active": 0},
            {"name": "Лекарства", "fixed": None, "min": 0.0, "weight": 6.0, "active": 0},
            {"name": "Посещение врача", "fixed": None, "min": 0.0, "weight": 6.0, "active": 0},
            {"name": "Фитнес-клуб, бассейн", "fixed": 3000.0, "min": 3000.0, "weight": 4.0, "active": 1},
            {"name": "Процедуры красоты", "fixed": None, "min": 0.0, "weight": 4.0, "active": 0},
            {"name": "Одежда и обувь", "fixed": None, "min": 1000.0, "weight": 4.0, "active": 1},
            {"name": "Электроника и гаджеты", "fixed": None, "min": 0.0, "weight": 4.0, "active": 0},
            {"name": "Аксессуары", "fixed": None, "min": 0.0, "weight": 4.0, "active": 0},
            {"name": "Ремонт и мебель", "fixed": None, "min": 0.0, "weight": 5.0, "active": 0},
            {"name": "Средства и услуги", "fixed": None, "min": 0.0, "weight": 4.0, "active": 0},
            {"name": "Кино, театры, концерты", "fixed": None, "min": 0.0, "weight": 3.0, "active": 0},
            {"name": "Игры и подписки", "fixed": None, "min": 0.0, "weight": 3.0, "active": 0},
            {"name": "Хобби", "fixed": None, "min": 1000.0, "weight": 3.0, "active": 1},
            {"name": "Поездки и путешествия", "fixed": None, "min": 0.0, "weight": 3.0, "active": 0},
            {"name": "Курсы, книги", "fixed": None, "min": 0.0, "weight": 5.0, "active": 0},
            {"name": "Онлайн-обучение", "fixed": 2000.0, "min": 2000.0, "weight": 5.0, "active": 1},
            {"name": "Вебинары и мастер-классы", "fixed": None, "min": 0.0, "weight": 5.0, "active": 0},
            {"name": "Подарки", "fixed": None, "min": 0.0, "weight": 4.0, "active": 0},
            {"name": "Прочее", "fixed": None, "min": 0.0, "weight": 2.0, "active": 0},
            {"name": "Сбережения", "fixed": None, "min": 0.0, "weight": 8.0, "active": 1},
        ]
        save_categories(categories)
    return categories

def save_categories(categories):
    init_db()
    conn = sqlite3.connect("budget.db")
    c = conn.cursor()
    c.execute("DELETE FROM categories")
    for cat in categories:
        c.execute("INSERT INTO categories (name, fixed, min, weight, active) VALUES (?, ?, ?, ?, ?)",
                  (cat["name"], cat["fixed"], cat["min"], cat["weight"], cat["active"]))
    conn.commit()
    conn.close()

def load_goals():
    init_db()
    conn = sqlite3.connect("budget.db")
    c = conn.cursor()
    c.execute("SELECT name, amount, term FROM goals")
    goals = [{"name": row[0], "amount": row[1], "term": row[2]} for row in c.fetchall()]
    conn.close()
    return goals

def save_goals(goals):
    init_db()
    conn = sqlite3.connect("budget.db")
    c = conn.cursor()
    c.execute("DELETE FROM goals")
    for goal in goals:
        c.execute("INSERT INTO goals VALUES (?, ?, ?)", (goal["name"], goal["amount"], goal["term"]))
    conn.commit()
    conn.close()

def calculate_annuity_payment(amount, term, rate):
    monthly_rate = rate / 12
    if monthly_rate == 0:
        return amount / term
    payment = amount * monthly_rate * (1 + monthly_rate) ** term / ((1 + monthly_rate) ** term - 1)
    return payment
