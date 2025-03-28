import random
import numpy as np
from history import load_budget_history

def initialize_population(pop_size, num_categories, income, debts, fixed_costs, min_costs, months, categories):
    """Инициализация популяции решений для нескольких месяцев."""
    population = []
    for _ in range(pop_size):
        solution = []
        remaining_debts = [d["remaining"] for d in debts]
        for _ in range(months):
            month_solution = []
            available = income - fixed_costs - sum(d["payment"] for d in debts if d["remaining"] > 0)
            for i in range(num_categories):
                if categories[i]["fixed"]:
                    month_solution.append(categories[i]["fixed"])
                else:
                    min_val = categories[i]["min"]
                    max_val = available if categories[i]["name"] == "Сбережения" else available / 2
                    month_solution.append(random.uniform(min_val, max_val))
            total = sum(month_solution)
            if total > income:
                scale = income / total
                month_solution = [x * scale for x in month_solution]
            solution.append(month_solution)
            # Обновляем долги для следующего месяца
            for d in debts:
                if d["remaining"] > 0:
                    interest = d["remaining"] * (d["rate"] / 12)
                    principal = d["payment"] - interest
                    d["remaining"] = max(0, d["remaining"] - principal)
        population.append(solution)
    return population

def fitness(solution, categories, income, debts, goals, history, weights=(0.4, 0.3, 0.3)):
    """Многоцелевая фитнес-функция: сбережения, долги, баланс."""
    savings_total = 0
    debt_remaining = sum(d["remaining"] for d in debts[:])  # Копия начальных долгов
    balance_score = 0
    total_weight = sum(c["weight"] for c in categories if not c["fixed"] and c["active"])

    for month_idx, month_solution in enumerate(solution):
        savings = month_solution[[c["name"] for c in categories].index("Сбережения")]
        savings_total += savings
        
        # Баланс расходов относительно весов
        variable_spend = sum(s for i, s in enumerate(month_solution) if not categories[i]["fixed"] and categories[i]["name"] != "Сбережения")
        if variable_spend > 0:
            balance_score += sum(abs(s - categories[i]["weight"] * variable_spend / total_weight) 
                               for i, s in enumerate(month_solution) if not categories[i]["fixed"] and categories[i]["active"])
        
        # Обновление долгов
        for d in debts:
            if d["remaining"] > 0:
                interest = d["remaining"] * (d["rate"] / 12)
                principal = d["payment"] - interest
                d["remaining"] = max(0, d["remaining"] - principal)

    # Учёт истории для адаптации
    history_factor = 0
    if history:
        avg_spend = {cat: sum(h[cat] for h in history) / len(history) for cat in history[0].keys() if cat != "income" and cat != "debts"}
        for month_solution in solution:
            for i, spend in enumerate(month_solution):
                if categories[i]["name"] in avg_spend:
                    history_factor += abs(spend - avg_spend[categories[i]["name"]]) / (avg_spend[categories[i]["name"]] + 1)

    # Цели
    goal_progress = savings_total / sum(g["amount"] for g in goals) if goals else 1

    # Многоцелевая оценка
    savings_score = savings_total
    debt_score = 1 / (debt_remaining + 1)  # Чем меньше долгов, тем лучше
    balance_score = 1 / (balance_score + 1)  # Чем меньше отклонение, тем лучше
    history_score = 1 / (history_factor + 1)  # Чем ближе к истории, тем лучше
    
    return (weights[0] * savings_score + weights[1] * debt_score + weights[2] * balance_score) * goal_progress * history_score

def crossover(parent1, parent2):
    """Скрещивание двух решений."""
    child = []
    for m1, m2 in zip(parent1, parent2):
        point = random.randint(0, len(m1))
        child.append(m1[:point] + m2[point:])
    return child

def mutate(solution, income, fixed_costs, min_costs, debts, categories):
    """Мутация решения."""
    for month_solution in solution:
        idx = random.randint(0, len(month_solution) - 1)
        if not categories[idx]["fixed"]:
            available = income - fixed_costs - sum(d["payment"] for d in debts if d["remaining"] > 0)
            month_solution[idx] = random.uniform(categories[idx]["min"], available / 2)
        total = sum(month_solution)
        if total > income:
            scale = income / total
            month_solution[:] = [x * scale for x in month_solution]
    return solution

def optimize_budget(income, categories, debts, goals, months=1, pop_size=100, generations=50):
    """Основная функция ГА для оптимизации бюджета."""
    fixed_costs = sum(c["fixed"] or 0 for c in categories if c["active"])
    min_costs = sum(c["min"] for c in categories if c["active"] and not c["fixed"])
    
    # Загрузка истории
    history = load_budget_history()
    if not history:
        history = None
    
    # Инициализация популяции
    population = initialize_population(pop_size, len(categories), income, debts, fixed_costs, min_costs, months, categories)
    
    # Эволюция
    for _ in range(generations):
        population = sorted(population, key=lambda x: fitness(x, categories, income, debts[:], goals, history), reverse=True)
        new_population = population[:pop_size // 2]  # Элитизм
        
        while len(new_population) < pop_size:
            parent1, parent2 = random.sample(population[:pop_size // 2], 2)
            child = crossover(parent1, parent2)
            if random.random() < 0.1:
                child = mutate(child, income, fixed_costs, min_costs, debts, categories)
            new_population.append(child)
        
        population = new_population
    
    # Лучшее решение
    best_solution = max(population, key=lambda x: fitness(x, categories, income, debts[:], goals, history))
    return best_solution
