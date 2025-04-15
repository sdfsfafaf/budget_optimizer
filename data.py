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
        {"name": "Аренда жилья / ипотека", "type": "fixed", "fixed": 30000.0, "regular": None, "min": 30000.0, "weight": 5.0, "mandatory": 0, "active": 1, "irregular_freq": 0.0},
        {"name": "Коммунальные услуги", "type": "fixed", "fixed": 5000.0, "regular": None, "min": 5000.0, "weight": 5.0, "mandatory": 0, "active": 1, "irregular_freq": 0.0},
        {"name": "Интернет и мобильная связь", "type": "fixed", "fixed": 1000.0, "regular": None, "min": 1000.0, "weight": 4.0, "mandatory": 0, "active": 1, "irregular_freq": 0.0},
        {"name": "Налоги и страховки", "type": "fixed", "fixed": 2000.0, "regular": None, "min": 2000.0, "weight": 4.0, "mandatory": 0, "active": 1, "irregular_freq": 0.0},
        {"name": "Фитнес-клуб, бассейн", "type": "fixed", "fixed": 3000.0, "regular": None, "min": 3000.0, "weight": 4.0, "mandatory": 0, "active": 1, "irregular_freq": 0.0},
        {"name": "Онлайн-обучение", "type": "fixed", "fixed": 2000.0, "regular": None, "min": 2000.0, "weight": 5.0, "mandatory": 0, "active": 1, "irregular_freq": 0.0},
        {"name": "Продукты", "type": "regular", "fixed": None, "regular": 15000.0, "min": 13500.0, "weight": 7.0, "mandatory": 0, "active": 1, "irregular_freq": 0.0},
        {"name": "Проезд", "type": "regular", "fixed": None, "regular": 3000.0, "min": 2700.0, "weight": 5.0, "mandatory": 0, "active": 1, "irregular_freq": 0.0},
        {"name": "Сбережения", "type": "regular", "fixed": None, "regular": 15000.0, "min": 13500.0, "weight": 10.0, "mandatory": 0, "active": 1, "irregular_freq": 0.0},
        {"name": "Прочее", "type": "regular", "fixed": None, "regular": 15000.0, "min": 13500.0, "weight": 3.0, "mandatory": 0, "active": 1, "irregular_freq": 0.0},
        {"name": "Хобби", "type": "irregular", "fixed": None, "regular": None, "min": 900.0, "weight": 2.0, "mandatory": 0, "active": 1, "irregular_freq": 0.2},
        {"name": "Кафе и рестораны", "type": "irregular", "fixed": None, "regular": None, "min": 1800.0, "weight": 2.0, "mandatory": 0, "active": 1, "irregular_freq": 0.3},
        {"name": "Одежда и обувь", "type": "irregular", "fixed": None, "regular": None, "min": 1000.0, "weight": 3.0, "mandatory": 0, "active": 1, "irregular_freq": 0.4},
        {"name": "Обслуживание и ремонт", "type": "irregular", "fixed": None, "regular": None, "min": 5000.0, "weight": 5.0, "mandatory": 1, "active": 0, "irregular_freq": 0.2},
        {"name": "Лекарства", "type": "irregular", "fixed": None, "regular": None, "min": 2000.0, "weight": 6.0, "mandatory": 1, "active": 0, "irregular_freq": 0.3},
        {"name": "Посещение врача", "type": "irregular", "fixed": None, "regular": None, "min": 3000.0, "weight": 6.0, "mandatory": 1, "active": 0, "irregular_freq": 0.2},
        {"name": "Ремонт и мебель", "type": "irregular", "fixed": None, "regular": None, "min": 10000.0, "weight": 5.0, "mandatory": 1, "active": 0, "irregular_freq": 0.1},
        {"name": "Электроника и гаджеты", "type": "irregular", "fixed": None, "regular": None, "min": 5000.0, "weight": 4.0, "mandatory": 0, "active": 0, "irregular_freq": 0.1},
        {"name": "Аксессуары", "type": "irregular", "fixed": None, "regular": None, "min": 1000.0, "weight": 4.0, "mandatory": 0, "active": 0, "irregular_freq": 0.2},
        {"name": "Процедуры красоты", "type": "irregular", "fixed": None, "regular": None, "min": 2000.0, "weight": 4.0, "mandatory": 0, "active": 0, "irregular_freq": 0.3},
        {"name": "Средства и услуги", "type": "irregular", "fixed": None, "regular": None, "min": 1000.0, "weight": 4.0, "mandatory": 0, "active": 0, "irregular_freq": 0.3},
        {"name": "Кино, театры, концерты", "type": "irregular", "fixed": None, "regular": None, "min": 1000.0, "weight": 3.0, "mandatory": 0, "active": 0, "irregular_freq": 0.4},
        {"name": "Игры и подписки", "type": "irregular", "fixed": None, "regular": None, "min": 500.0, "weight": 3.0, "mandatory": 0, "active": 0, "irregular_freq": 0.5},
        {"name": "Поездки и путешествия", "type": "irregular", "fixed": None, "regular": None, "min": 10000.0, "weight": 3.0, "mandatory": 0, "active": 0, "irregular_freq": 0.2},
        {"name": "Курсы, книги", "type": "irregular", "fixed": None, "regular": None, "min": 2000.0, "weight": 5.0, "mandatory": 0, "active": 0, "irregular_freq": 0.3},
        {"name": "Вебинары и мастер-классы", "type": "irregular", "fixed": None, "regular": None, "min": 2000.0, "weight": 5.0, "mandatory": 0, "active": 0, "irregular_freq": 0.2},
        {"name": "Подарки", "type": "irregular", "fixed": None, "regular": None, "min": 1000.0, "weight": 4.0, "mandatory": 0, "active": 0, "irregular_freq": 0.3},
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