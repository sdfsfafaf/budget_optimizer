import json
import os

DATA_DIR = "data"
CATEGORIES_FILE = os.path.join(DATA_DIR, "categories.json")
GOALS_FILE = os.path.join(DATA_DIR, "goals.json")

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def load_categories():
    ensure_data_dir()
    if os.path.exists(CATEGORIES_FILE):
        with open(CATEGORIES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return [
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
        {"name": "Сбережения", "fixed": None, "min": 0.0, "weight": 8.0, "active": 1}
    ]

def save_categories(categories):
    ensure_data_dir()
    with open(CATEGORIES_FILE, "w", encoding="utf-8") as f:
        json.dump(categories, f, ensure_ascii=False, indent=4)

def load_goals():
    ensure_data_dir()
    if os.path.exists(GOALS_FILE):
        with open(GOALS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_goals(goals):
    ensure_data_dir()
    with open(GOALS_FILE, "w", encoding="utf-8") as f:
        json.dump(goals, f, ensure_ascii=False, indent=4)

def calculate_annuity_payment(amount, term, rate):
    monthly_rate = rate / 12
    if monthly_rate == 0:
        return round(amount / term, 2)
    payment = amount * monthly_rate * (1 + monthly_rate) ** term / ((1 + monthly_rate) ** term - 1)
    return round(payment, 2)
