# history.py
import sqlite3
import random
from datetime import datetime, timedelta


def init_db():
    conn = sqlite3.connect("budget.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month TEXT,
            amount REAL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            fixed REAL,
            min REAL,
            weight REAL,
            active INTEGER DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month TEXT,
            category TEXT,
            amount REAL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            total REAL,
            months INTEGER,
            interest_rate REAL,
            monthly_payment REAL,
            remaining_amount REAL,
            remaining_months INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            amount REAL,
            months INTEGER
        )
    """)

    conn.commit()
    conn.close()


def populate_default_categories():
    default_categories = [
        {"name": "Аренда жилья / ипотека", "fixed": 30000, "min": 30000, "weight": 5, "active": 1},
        {"name": "Коммунальные услуги", "fixed": 5000, "min": 5000, "weight": 5, "active": 1},
        {"name": "Интернет и мобильная связь", "fixed": 1000, "min": 1000, "weight": 4, "active": 1},
        {"name": "Налоги и страховки", "fixed": 2000, "min": 2000, "weight": 4, "active": 1},
        {"name": "Продукты", "fixed": None, "min": 15000, "weight": 7, "active": 1},
        {"name": "Кафе и рестораны", "fixed": None, "min": 2000, "weight": 3, "active": 1},
        {"name": "Проезд", "fixed": None, "min": 3000, "weight": 5, "active": 1},
        {"name": "Обслуживание и ремонт", "fixed": None, "min": 0, "weight": 5, "active": 0},
        {"name": "Лекарства", "fixed": None, "min": 0, "weight": 6, "active": 0},
        {"name": "Посещение врача", "fixed": None, "min": 0, "weight": 6, "active": 0},
        {"name": "Фитнес-клуб, бассейн", "fixed": 3000, "min": 3000, "weight": 4, "active": 1},
        {"name": "Процедуры красоты", "fixed": None, "min": 0, "weight": 4, "active": 0},
        {"name": "Одежда и обувь", "fixed": None, "min": 1000, "weight": 4, "active": 1},
        {"name": "Электроника и гаджеты", "fixed": None, "min": 0, "weight": 4, "active": 0},
        {"name": "Аксессуары", "fixed": None, "min": 0, "weight": 4, "active": 0},
        {"name": "Ремонт и мебель", "fixed": None, "min": 0, "weight": 5, "active": 0},
        {"name": "Средства и услуги", "fixed": None, "min": 0, "weight": 4, "active": 0},
        {"name": "Кино, театры, концерты", "fixed": None, "min": 0, "weight": 3, "active": 0},
        {"name": "Игры и подписки", "fixed": None, "min": 0, "weight": 3, "active": 0},
        {"name": "Хобби", "fixed": None, "min": 1000, "weight": 3, "active": 1},
        {"name": "Поездки и путешествия", "fixed": None, "min": 0, "weight": 3, "active": 0},
        {"name": "Курсы, книги", "fixed": None, "min": 0, "weight": 5, "active": 0},
        {"name": "Онлайн-обучение", "fixed": 2000, "min": 2000, "weight": 5, "active": 1},
        {"name": "Вебинары и мастер-классы", "fixed": None, "min": 0, "weight": 5, "active": 0},
        {"name": "Подарки", "fixed": None, "min": 0, "weight": 4, "active": 0},
        {"name": "Прочее", "fixed": None, "min": 0, "weight": 2, "active": 0},
        {"name": "Сбережения", "fixed": None, "min": 0, "weight": 8, "active": 1}
    ]
    conn = sqlite3.connect("budget.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM categories")
    for cat in default_categories:
        cursor.execute("INSERT INTO categories (name, fixed, min, weight, active) VALUES (?, ?, ?, ?, ?)",
                       (cat["name"], cat["fixed"], cat["min"], cat["weight"], cat["active"]))
    conn.commit()
    conn.close()


def add_income(month, amount):
    conn = sqlite3.connect("budget.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO income (month, amount) VALUES (?, ?)", (month, amount))
    conn.commit()
    conn.close()


def get_income(month=None):
    conn = sqlite3.connect("budget.db")
    cursor = conn.cursor()
    if month:
        cursor.execute("SELECT amount FROM income WHERE month = ? ORDER BY id DESC LIMIT 1", (month,))
    else:
        cursor.execute("SELECT amount FROM income ORDER BY id DESC LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def add_category(name, fixed=None, min=0, weight=1, active=1):
    conn = sqlite3.connect("budget.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO categories (name, fixed, min, weight, active) VALUES (?, ?, ?, ?, ?)",
                   (name, fixed, min, weight, active))
    conn.commit()
    conn.close()


def remove_category(name):
    conn = sqlite3.connect("budget.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM categories WHERE name = ? AND name != 'Сбережения'", (name,))
    conn.commit()
    conn.close()


def get_categories():
    conn = sqlite3.connect("budget.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, fixed, min, weight, active FROM categories")
    categories = [{"name": row[0], "fixed": row[1], "min": row[2], "weight": row[3], "active": row[4]}
                  for row in cursor.fetchall()]
    conn.close()
    return categories


def add_expenses(month, categories, amounts, conn=None):
    if conn is None:
        conn = sqlite3.connect("budget.db")
        cursor = conn.cursor()
        close_conn = True
    else:
        cursor = conn.cursor()
        close_conn = False

    for cat, amt in zip(categories, amounts):
        if cat["active"]:
            cursor.execute("INSERT INTO expenses (month, category, amount) VALUES (?, ?, ?)",
                           (month, cat["name"], amt))

    if close_conn:
        conn.commit()
        conn.close()


def add_or_update_debt(name, total, months, interest_rate, monthly_payment):
    conn = sqlite3.connect("budget.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM debts WHERE name = ?", (name,))
    if cursor.fetchone():
        cursor.execute(
            "UPDATE debts SET total = ?, months = ?, interest_rate = ?, monthly_payment = ?, remaining_amount = ?, remaining_months = ? WHERE name = ?",
            (total, months, interest_rate, monthly_payment, total, months, name))
    else:
        cursor.execute(
            "INSERT INTO debts (name, total, months, interest_rate, monthly_payment, remaining_amount, remaining_months) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, total, months, interest_rate, monthly_payment, total, months))
    conn.commit()
    conn.close()


def get_expense_history():
    conn = sqlite3.connect("budget.db")
    cursor = conn.cursor()
    cursor.execute("SELECT category, AVG(amount) FROM expenses GROUP BY category")
    history = dict(cursor.fetchall())
    conn.close()
    return history


def get_debts():
    conn = sqlite3.connect("budget.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name, total, months, interest_rate, monthly_payment, remaining_amount, remaining_months FROM debts")
    debts = [{"name": row[0], "total": row[1], "months": row[2], "interest_rate": row[3],
              "monthly_payment": row[4], "remaining_amount": row[5], "remaining_months": row[6]}
             for row in cursor.fetchall()]
    conn.close()
    return debts


def update_debt_after_payment():
    conn = sqlite3.connect("budget.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, remaining_amount, monthly_payment, remaining_months FROM debts")
    debts = cursor.fetchall()
    for name, remaining_amount, monthly_payment, remaining_months in debts:
        if remaining_months > 0:
            new_remaining = max(0, remaining_amount - monthly_payment)
            new_months = remaining_months - 1 if new_remaining > 0 else 0
            cursor.execute("UPDATE debts SET remaining_amount = ?, remaining_months = ? WHERE name = ?",
                           (new_remaining, new_months, name))
            if new_remaining == 0:
                cursor.execute("DELETE FROM debts WHERE name = ?", (name,))
    conn.commit()
    conn.close()


def add_goal(name, amount, months):
    conn = sqlite3.connect("budget.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO goals (name, amount, months) VALUES (?, ?, ?)",
                   (name, amount, months))
    conn.commit()
    conn.close()


def get_goals():
    conn = sqlite3.connect("budget.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, amount, months FROM goals")
    goals = [{"name": row[0], "amount": row[1], "months": row[2]} for row in cursor.fetchall()]
    conn.close()
    return goals


def populate_history(months_back=3):
    conn = sqlite3.connect("budget.db")
    cursor = conn.cursor()
    categories = get_categories()
    current_date = datetime.now()

    for i in range(months_back):
        month = (current_date - timedelta(days=30 * (i + 1))).strftime("%Y-%m")
        income = 100000 + random.randint(-5000, 5000)
        cursor.execute("INSERT OR IGNORE INTO income (month, amount) VALUES (?, ?)", (month, income))

        total_fixed = sum(cat["fixed"] or 0 for cat in categories if cat["fixed"] and cat["active"])
        remaining = income - total_fixed
        variable_active = [cat for cat in categories if cat["fixed"] is None and cat["active"]]

        amounts = [0] * len(categories)
        for j, cat in enumerate(categories):
            if cat["active"]:
                if cat["fixed"]:
                    amounts[j] = cat["fixed"]
                elif cat["name"] != "Сбережения" and remaining > 0:
                    value = max(cat["min"], random.randint(0, min(remaining // len(variable_active), 10000)))
                    amounts[j] = value
                    remaining -= value

        savings_idx = next(i for i, cat in enumerate(categories) if cat["name"] == "Сбережения")
        amounts[savings_idx] = remaining

        add_expenses(month, categories, amounts, conn)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    populate_default_categories()
    populate_history()