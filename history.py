import sqlite3
from datetime import datetime, timedelta

DB_FILE = "budget.db"

def load_income_history():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS income (month TEXT PRIMARY KEY, amount REAL)")
    cursor.execute("SELECT month, amount FROM income")
    history = dict(cursor.fetchall())
    if not history:
        num_months = int(input("На сколько месяцев заполнить историю доходов? "))
        amount = float(input("Введите доход (будет применён ко всем месяцам): "))
        for i in range(num_months):
            month = (datetime.now() + timedelta(days=30 * i)).strftime("%Y-%m")
            cursor.execute("INSERT OR REPLACE INTO income (month, amount) VALUES (?, ?)", (month, amount))
        conn.commit()
        cursor.execute("SELECT month, amount FROM income")
        history = dict(cursor.fetchall())
    conn.close()
    return history

def update_debt_after_payment(amount, payment, term, rate):
    monthly_rate = rate / 12
    interest = amount * monthly_rate
    principal = payment - interest
    new_amount = max(0, amount - principal)
    new_term = term - 1
    return new_amount, new_term

def save_budget_to_history(month, income, budget, debt_payment):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budget (
            month TEXT,
            category TEXT,
            amount REAL,
            PRIMARY KEY (month, category)
        )
    """)
    cursor.execute("CREATE TABLE IF NOT EXISTS debt_payments (month TEXT PRIMARY KEY, amount REAL)")
    
    from data import load_categories
    categories = load_categories()
    for i, amount in enumerate(budget):
        if amount > 0 and categories[i]["active"]:
            cursor.execute(
                "INSERT OR REPLACE INTO budget (month, category, amount) VALUES (?, ?, ?)",
                (month, categories[i]["name"], amount)
            )
    if debt_payment > 0:
        cursor.execute(
            "INSERT OR REPLACE INTO debt_payments (month, amount) VALUES (?, ?)",
            (month, debt_payment)
        )
    conn.commit()
    conn.close()
