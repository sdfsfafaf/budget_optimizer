import random
import numpy as np
from history import load_budget_history


def initialize_population(pop_size, num_categories, income, debts, fixed_costs, min_costs, months, categories):
    population = []
    for _ in range(pop_size):
        solution = []
        temp_debts = [{"remaining": d["remaining"], "payment": d["payment"], "rate": d["rate"]} for d in debts]
        for _ in range(months):
            month_solution = []
            debt_payment = sum(d["payment"] for d in temp_debts if d["remaining"] > 0)
            available = income - fixed_costs - debt_payment
            if available < min_costs:
                available = min_costs  # Минимальные траты должны быть покрыты
            remaining = available
            for i in range(num_categories):
                if categories[i]["fixed"]:
                    month_solution.append(categories[i]["fixed"])
                else:
                    min_val = categories[i]["min"]
                    if i == num_categories - 1:  # Последняя категория (Сбережения)
                        month_solution.append(remaining)
                    else:
                        max_val = min(remaining - sum(c["min"] for c in categories[i+1:] if not c["fixed"]), available / 2)
                        val = random.uniform(min_val, max_val) if max_val > min_val else min_val
                        month_solution.append(val)
                        remaining -= val
            solution.append(month_solution)
            for d in temp_debts:
                if d["remaining"] > 0:
                    interest = d["remaining"] * (d["rate"] / 12)
                    principal = d["payment"] - interest
                    d["remaining"] = max(0, d["remaining"] - principal)
        population.append(solution)
    return population

def mutate(solution, income, fixed_costs, min_costs, debts, categories):
    temp_debts = [{"remaining": d["remaining"], "payment": d["payment"], "rate": d["rate"]} for d in debts]
    for month_idx, month_solution in enumerate(solution):
        debt_payment = sum(d["payment"] for d in temp_debts if d["remaining"] > 0)
        available = income - fixed_costs - debt_payment
        if available < min_costs:
            available = min_costs
        idx = random.randint(0, len(month_solution) - 1)
        if not categories[idx]["fixed"]:
            remaining = available - sum(s for i, s in enumerate(month_solution) if i != idx and not categories[i]["fixed"])
            min_val = categories[idx]["min"]
            max_val = remaining if categories[idx]["name"] == "Сбережения" else remaining / 2
            month_solution[idx] = random.uniform(min_val, max_val) if max_val > min_val else min_val
        total = sum(month_solution) + debt_payment
        if total > income:
            scale = (income - debt_payment) / sum(month_solution)
            for i in range(len(month_solution)):
                if not categories[i]["fixed"]:
                    month_solution[i] *= scale
        for d in temp_debts:
            if d["remaining"] > 0:
                interest = d["remaining"] * (d["rate"] / 12)
                principal = d["payment"] - interest
                d["remaining"] = max(0, d["remaining"] - principal)
    return solution


def fitness(solution, categories, income, debts, goals, history, weights=(0.4, 0.3, 0.3)):
    savings_total = 0
    temp_debts = [{"remaining": d["remaining"], "payment": d["payment"], "rate": d["rate"]} for d in debts]
    debt_remaining = sum(d["remaining"] for d in temp_debts)
    balance_score = 0
    fixed_penalty = 0
    total_weight = sum(c["weight"] for c in categories if not c["fixed"] and c["active"])
    savings_idx = next(i for i, cat in enumerate(categories) if cat["name"] == "Сбережения")

    for month_idx, month_solution in enumerate(solution):
        savings = month_solution[savings_idx]
        savings_total += savings

        for i, cat in enumerate(categories):
            if cat["fixed"] and month_solution[i] != cat["fixed"]:
                fixed_penalty += abs(month_solution[i] - cat["fixed"])

        variable_spend = sum(s for i, s in enumerate(month_solution) if not categories[i]["fixed"] and categories[i]["name"] != "Сбережения")
        if variable_spend > 0:
            balance_score += sum(abs(s - categories[i]["weight"] * variable_spend / total_weight)
                                 for i, s in enumerate(month_solution) if not categories[i]["fixed"] and categories[i]["active"])

        debt_payment = sum(d["payment"] for d in temp_debts if d["remaining"] > 0)
        total_spend = sum(month_solution) + debt_payment
        if total_spend > income:
            balance_score += (total_spend - income) * 100  # Штраф за превышение дохода

        for d in temp_debts:
            if d["remaining"] > 0:
                interest = d["remaining"] * (d["rate"] / 12)
                principal = d["payment"] - interest
                d["remaining"] = max(0, d["remaining"] - principal)

    history_factor = 0
    if history:
        avg_spend = {}
        for i, cat in enumerate(categories):
            cat_name = cat["name"]
            avg_spend[cat_name] = sum(h.get(cat_name, 0) for h in history) / len(history)
        for month_solution in solution:
            for i, spend in enumerate(month_solution):
                cat_name = categories[i]["name"]
                if cat_name in avg_spend:
                    history_factor += abs(spend - avg_spend[cat_name]) / (avg_spend[cat_name] + 1)

    goal_progress = savings_total / sum(g["amount"] for g in goals) if goals else 1
    savings_score = savings_total
    debt_score = 1 / (debt_remaining + 1)
    balance_score = 1 / (balance_score + 1)
    history_score = 1 / (history_factor + 1)
    fixed_score = 1 / (fixed_penalty + 1)

    # Увеличиваем влияние целей и долгов
    return (weights[0] * savings_score * goal_progress + weights[1] * debt_score + weights[2] * balance_score) * history_score * fixed_score


def crossover(parent1, parent2):
    child = []
    for m1, m2 in zip(parent1, parent2):
        point = random.randint(0, len(m1))
        child.append(m1[:point] + m2[point:])
    return child


def optimize_budget(income, categories, debts, goals, months=1, pop_size=100, generations=50):
    fixed_costs = sum(c["fixed"] or 0 for c in categories if c["active"])
    min_costs = sum(c["min"] for c in categories if c["active"] and not c["fixed"])

    history = load_budget_history()
    if not history:
        history = None

    population = initialize_population(pop_size, len(categories), income, debts, fixed_costs, min_costs, months, categories)

    for _ in range(generations):
        population = sorted(population, key=lambda x: fitness(x, categories, income, debts[:], goals, history), reverse=True)
        new_population = population[:pop_size // 2]

        while len(new_population) < pop_size:
            parent1, parent2 = random.sample(population[:pop_size // 2], 2)
            child = crossover(parent1, parent2)
            if random.random() < 0.1:
                child = mutate(child, income, fixed_costs, min_costs, debts, categories)
            new_population.append(child)

        population = new_population

    best_solution = max(population, key=lambda x: fitness(x, categories, income, debts[:], goals, history))

    # Обновляем долги только в конце
    temp_debts = [{"remaining": d["remaining"], "payment": d["payment"], "rate": d["rate"]} for d in debts]
    for month_solution in best_solution:
        for d in temp_debts:
            if d["remaining"] > 0:
                interest = d["remaining"] * (d["rate"] / 12)
                principal = d["payment"] - interest
                d["remaining"] = max(0, d["remaining"] - principal)
                if d["remaining"] <= 0:
                    d["payment"] = 0
    for i, d in enumerate(debts):
        d["remaining"] = temp_debts[i]["remaining"]
        d["payment"] = temp_debts[i]["payment"]

    return best_solution, debts