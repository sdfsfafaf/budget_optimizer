import sqlite3
import os.path

def init_db():
    if not os.path.exists("budget.db"):
        conn = sqlite3.connect("budget.db")
        c = conn.cursor()
        c.execute('''CREATE TABLE categories
                     (name TEXT, fixed REAL, min REAL, weight REAL, active INTEGER)''')
        c.execute('''CREATE TABLE goals
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
            {"name": "Еда", "fixed": None, "min": 5000, "weight": 8, "active": 1},
            {"name": "Транспорт", "fixed": None, "min": 1000, "weight": 5, "active": 1},
            {"name": "Развлечения", "fixed": None, "min": 1000, "weight": 3, "active": 1},
            {"name": "Сбережения", "fixed": None, "min": 0, "weight": 10, "active": 1},
        ]
        save_categories(categories)
    return categories

def save_categories(categories):
    init_db()
    conn = sqlite3.connect("budget.db")
    c = conn.cursor()
    c.execute("DELETE FROM categories")
    for cat in categories:
        c.execute("INSERT INTO categories VALUES (?, ?, ?, ?, ?)",
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
