import random
from history import load_budget_history

def select_parents(population, fitness_scores, num_parents=None):
    if num_parents is None:
        num_parents = len(population) // 2
    parents = []
    for _ in range(num_parents):
        max_fitness_idx = fitness_scores.index(max(fitness_scores))
        parents.append(population[max_fitness_idx])
        fitness_scores[max_fitness_idx] = -float('inf')
    return parents

def fitness(solution, categories, income, debts, goals, history, weights=(0.5, 0.4, 0.1)):
    savings_total = 0
    temp_debts = [{"remaining": d["remaining"], "payment": d["payment"], "rate": d["rate"]} for d in debts]
    debt_remaining = sum(d["remaining"] for d in temp_debts)
    balance_score = 0
    fixed_penalty = 0
    total_weight = sum(c["weight"] for c in categories if not c["fixed"] and c["active"])
    savings_idx = next(i for i, cat in enumerate(categories) if cat["name"] == "Сбережения")
    debt_closed_months = 0
    total_interest = 0

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
            balance_score += (total_spend - income) * 100

        for d in temp_debts:
            if d["remaining"] > 0:
                interest = d["remaining"] * (d["rate"] / 12)
                total_interest += interest
                principal = d["payment"] - interest
                d["remaining"] = max(0, d["remaining"] - principal)
                if d["remaining"] <= 0 and debt_closed_months == 0:
                    debt_closed_months = month_idx + 1

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
    savings_score = savings_total * goal_progress
    debt_score = (1 / (debt_remaining + 1)) * (len(solution) / (debt_closed_months + 1) if debt_closed_months > 0 else 1) / (total_interest + 1)
    balance_score = 1 / (balance_score + 1)
    history_score = 1 / (history_factor + 1)
    fixed_score = 1 / (fixed_penalty + 1)

    return (weights[0] * savings_score + weights[1] * debt_score + weights[2] * balance_score) * history_score * fixed_score

def crossover(parent1, parent2):
    child1 = []
    child2 = []
    for m1, m2 in zip(parent1, parent2):
        point = random.randint(0, len(m1))
        child1.append(m1[:point] + m2[point:])
        child2.append(m2[:point] + m1[point:])
    return child1, child2

def mutate(solution, categories, income, debts):
    temp_debts = [{"remaining": d["remaining"], "payment": d["payment"], "rate": d["rate"]} for d in debts]
    for month_idx, month_solution in enumerate(solution):
        debt_payment = sum(d["payment"] for d in temp_debts if d["remaining"] > 0)
        available_income = income - debt_payment
        total_fixed = sum(cat["fixed"] for cat in categories if cat["fixed"] and cat["active"])

        # Мутация
        idx = random.randint(0, len(month_solution) - 1)
        if not categories[idx]["fixed"]:
            remaining = available_income - sum(s for i, s in enumerate(month_solution) if i != idx and not categories[i]["fixed"])
            min_val = categories[idx]["min"]
            max_val = remaining if categories[idx]["name"] == "Сбережения" else remaining / 2
            month_solution[idx] = max(min_val, random.uniform(min_val, max_val)) if max_val > min_val else min_val

        # Корректировка превышения
        total = sum(month_solution) + debt_payment
        if total > income:
            scale = (income - debt_payment - total_fixed) / sum(s for i, s in enumerate(month_solution) if not categories[i]["fixed"])
            for i in range(len(month_solution)):
                if not categories[i]["fixed"]:
                    month_solution[i] = max(categories[i]["min"], month_solution[i] * scale)

        # Обновление долгов
        for d in temp_debts:
            if d["remaining"] > 0:
                interest = d["remaining"] * (d["rate"] / 12)
                principal = min(d["payment"], d["remaining"] + interest) - interest
                d["remaining"] = max(0, d["remaining"] - principal)
                if d["remaining"] <= 0:
                    d["payment"] = 0

    return solution

def optimize_budget(income, categories, debts, goals, months=1):
    def initialize_population(pop_size):
        population = []
        fixed_total = sum(cat["fixed"] for cat in categories if cat["fixed"] and cat["active"])
        debt_payment = sum(d["payment"] for d in debts if d["remaining"] > 0)
        available_income = income - debt_payment

        for _ in range(pop_size):
            solution = []
            temp_debts = [{"remaining": d["remaining"], "payment": d["payment"], "rate": d["rate"]} for d in debts]
            for _ in range(months):
                month_solution = []
                remaining = available_income - fixed_total
                total_min = sum(cat["min"] for cat in categories if not cat["fixed"] and cat["active"])

                for cat in categories:
                    if cat["fixed"] and cat["active"]:
                        month_solution.append(cat["fixed"])
                    elif cat["active"]:
                        min_spend = cat["min"]
                        max_spend = min(remaining, remaining * cat["weight"] / sum(c["weight"] for c in categories if not c["fixed"] and c["active"])) if remaining > min_spend else min_spend
                        spend = random.uniform(min_spend, max_spend) if max_spend > min_spend else min_spend
                        month_solution.append(spend)
                        remaining -= spend
                    else:
                        month_solution.append(0)

                # Корректировка превышения
                total = sum(month_solution) + debt_payment
                if total > income:
                    scale = (income - debt_payment - fixed_total) / sum(s for i, s in enumerate(month_solution) if not categories[i]["fixed"])
                    for i in range(len(month_solution)):
                        if not categories[i]["fixed"]:
                            month_solution[i] = max(categories[i]["min"], month_solution[i] * scale)

                solution.append(month_solution)

                # Обновление долгов для следующего месяца
                for d in temp_debts:
                    if d["remaining"] > 0:
                        interest = d["remaining"] * (d["rate"] / 12)
                        principal = min(d["payment"], d["remaining"] + interest) - interest
                        d["remaining"] = max(0, d["remaining"] - principal)
                        if d["remaining"] <= 0:
                            d["payment"] = 0
            population.append(solution)
        return population

    pop_size = 100
    generations = 200
    population = initialize_population(pop_size)
    for _ in range(generations):
        fitness_scores = [fitness(ind, categories, income, debts, goals, history=None) for ind in population]
        parents = select_parents(population, fitness_scores)
        offspring = []
        for i in range(0, len(parents), 2):
            if i + 1 < len(parents):
                child1, child2 = crossover(parents[i], parents[i + 1])
                offspring.append(mutate(child1, categories, income, debts))
                offspring.append(mutate(child2, categories, income, debts))
        population = parents + offspring[:pop_size - len(parents)]

    best_solution = max(population, key=lambda x: fitness(x, categories, income, debts, goals, history=None))
    return best_solution, debts