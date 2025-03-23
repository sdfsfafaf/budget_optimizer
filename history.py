import sqlite3
import os
from datetime import datetime

DB_PATH = "budget.db"

def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS budget_history (month TEXT, category TEXT, amount REAL)")
        c.execute("CREATE TABLE IF NOT EXISTS income_history (month TEXT, income REAL)")
        conn.commit()
        conn.close()

def load_income_history():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT month, income FROM income_history")
    history = {row[0]: row[1] for row in c.fetchall()}
    conn.close()
    return history

def update_debt_after_payment(remaining, payment, term):
    remaining -= payment
    term -= 1
    return max(0, remaining), max(0, term)

def save_budget_to_history(month, income, allocations, debt_payment):
    init_db()
    from data import load_categories
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO income_history VALUES (?, ?)", (month, income))
    categories = load_categories()
    for i, amount in enumerate(allocations):
        if i < len(categories) and categories[i]["active"]:
            c.execute("INSERT INTO budget_history VALUES (?, ?, ?)", (month, categories[i]["name"], amount))
    if debt_payment > 0:
        c.execute("INSERT INTO budget_history VALUES (?, ?, ?)", (month, "Долги", debt_payment))
    conn.commit()
    conn.close()
