import sqlite3
import os
from datetime import datetime

DB_PATH = "budget.db"

def load_income_history():
    if not os.path.exists(DB_PATH):
        return {}
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
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS budget_history (month TEXT, category TEXT, amount REAL)")
    c.execute("CREATE TABLE IF NOT EXISTS income_history (month TEXT, income REAL)")
    c.execute("INSERT OR REPLACE INTO income_history VALUES (?, ?)", (month, income))
    for cat, amount in allocations.items():
        c.execute("INSERT INTO budget_history VALUES (?, ?, ?)", (month, cat, amount))
    conn.commit()
    conn.close()
