import random
from history import load_budget_history


def select_parents(population, fitness_scores, num_parents=None):
    """
    Выбирает родителей для скрещивания.
    """
    if num_parents is None:
        num_parents = len(population) // 2
    parents = []
    for _ in range(num_parents):
        max_fitness_idx = fitness_scores.index(max(fitness_scores))
        parents.append(population[max_fitness_idx])
        fitness_scores[max_fitness_idx] = -float('inf')
    return parents


def fitness(solution, categories, income, debts, goals, history, weights=(0.4, 0.3, 0.3)):
    """
    Оценивает качество распределения бюджета.
    - Сбережения: ±5% от 25 000 до цели, затем 0.
    - Регулярные траты: ±10%.
    - Нерегулярные траты: до 10% до цели, до 30% после.
    - Долги: аннуитетные.
    - Цель: ~300 000 ± 5%, штраф 500 за превышение.
    """
    savings_total = 0
    accumulated_savings = 0
    temp_debts = [{"remaining": d["remaining"], "payment": d["payment"], "rate": d["rate"]} for d in debts]
    debt_remaining = sum(d["remaining"] for d in temp_debts)
    total_interest = 0
    debt_closed_months = 0
    savings_idx = next(i for i, cat in enumerate(categories) if cat["name"] == "Сбережения")

    balance_score = 0
    fixed_penalty = 0
    regular_variance_penalty = 0
    mandatory_irregular_penalty = 0
    irregular_penalty = 0
    irregular_score = 0
    history_score = 0
    goal_score = 0
    savings_list = []

    # Кэшируем минимальные траты
    min_fixed = sum(cat["fixed"] for cat in categories if cat["fixed"] is not None and cat["active"])
    min_regular = sum(cat["min"] for cat in categories if cat["regular"] is not None and cat["active"])
    min_mandatory_irregular = sum(cat["min"] for cat in categories if cat["type"] == "irregular" and cat["mandatory"] and cat["active"])

    for month_idx in range(len(solution)):
        # Обнуляем сбережения после цели
        if accumulated_savings >= goals[0]["amount"]:
            solution[month_idx][savings_idx] = 0
        savings = solution[month_idx][savings_idx]
        savings_total += savings
        accumulated_savings += savings
        savings_list.append(savings)

        # Штрафы по категориям
        for i, cat in enumerate(categories):
            if cat["fixed"] is not None and cat["active"] and solution[month_idx][i] != cat["fixed"]:
                fixed_penalty += abs(solution[month_idx][i] - cat["fixed"]) / income
            elif cat["regular"] is not None and cat["active"]:
                avg_regular = cat["regular"]
                if abs(solution[month_idx][i] - avg_regular) > avg_regular * 0.1:
                    regular_variance_penalty += 2 * abs(solution[month_idx][i] - avg_regular) / income
            elif cat["type"] == "irregular" and cat["mandatory"] and cat["active"] and solution[month_idx][i] < cat["min"]:
                mandatory_irregular_penalty += (cat["min"] - solution[month_idx][i]) / income
            elif cat["type"] == "irregular" and solution[month_idx][i] > income * 0.1 and accumulated_savings < goals[0]["amount"]:
                irregular_penalty += (solution[month_idx][i] - income * 0.1) / income

        # Поощрение нерегулярных трат после цели
        if accumulated_savings >= goals[0]["amount"]:
            irregular_score += 2 * sum(solution[month_idx][i] for i, cat in enumerate(categories) if cat["type"] == "irregular") / (income * 0.3)

        # Аннуитетные платежи
        debt_payment = sum(d["payment"] for d in temp_debts if d["remaining"] > 0)
        if abs(debt_payment - sum(d["payment"] for d in debts if d["remaining"] > 0)) > 0.01:
            balance_score += 10 * abs(debt_payment - sum(d["payment"] for d in debts)) / income
        total_spend = sum(solution[month_idx]) + debt_payment
        if total_spend > income:
            balance_score += (total_spend - income) / income

        # Целевое значение сбережений
        target_savings = (income * 0.1) if any(d["remaining"] > 0 for d in temp_debts) else \
                         (goals[0]["amount"] / goals[0]["term"] if goals and accumulated_savings < goals[0]["amount"] else 0)
        if abs(savings - target_savings) > target_savings * 0.05 and savings > 0:
            balance_score += 4 * abs(savings - target_savings) / income

        # Обновление долгов
        for d in temp_debts:
            if d["remaining"] > 0:
                interest = d["remaining"] * (d["rate"] / 12)
                total_interest += interest
                principal = d["payment"] - interest
                d["remaining"] = max(0, d["remaining"] - principal)
                if d["remaining"] <= 0 and debt_closed_months == 0:
                    debt_closed_months = month_idx + 1

    # Штраф за вариативность сбережений
    savings_variance = sum((s - target_savings) ** 2 for s in savings_list if s > 0) / max(1, len([s for s in savings_list if s > 0]))
    savings_variance_penalty = 1 / (1 + savings_variance / (income * 0.05) ** 2)

    # Штраф за вариативность нерегулярных трат
    irregular_variance = sum(
        sum((month_solution[i] - cat["min"]) ** 2 for i, cat in enumerate(categories) if cat["type"] == "irregular" and month_solution[i] > 0)
        for month_solution in solution
    ) / (len(solution) * len(categories))
    irregular_penalty_factor = 1 / (1 + irregular_variance / (income * 0.1) ** 2)

    # Оценка цели
    if goals:
        for goal in goals:
            goal_progress = min(1, accumulated_savings / goal["amount"])
            if accumulated_savings > goal["amount"]:
                goal_score -= 500 * (accumulated_savings - goal["amount"]) / income
            goal_score += goal_progress
        goal_score /= len(goals)
    else:
        goal_score = 1

    savings_score = savings_total / income if accumulated_savings < goals[0]["amount"] else 0
    debt_score = (1 / (debt_remaining + 1)) * (len(solution) / (debt_closed_months + 1) if debt_closed_months else 1)
    balance_penalty = 1 / (balance_score + 1)
    fixed_penalty_factor = 1 / (fixed_penalty + 1)
    regular_penalty_factor = 1 / (regular_variance_penalty + 1)
    mandatory_penalty_factor = 1 / (mandatory_irregular_penalty + 1)
    history_factor = 1 / (history_score + 1) if history else 1

    total_fitness = (
        weights[0] * savings_score +
        weights[1] * debt_score +
        weights[2] * goal_score +
        0.2 * irregular_score
    ) * balance_penalty * fixed_penalty_factor * regular_penalty_factor * \
      mandatory_penalty_factor * history_factor * savings_variance_penalty * irregular_penalty_factor

    return total_fitness


def crossover(parent1, parent2, categories, goals):
    """
    Скрещивает родителей с учётом цели.
    """
    savings_idx = next(i for i, cat in enumerate(categories) if cat["name"] == "Сбережения")
    child1 = []
    child2 = []
    accumulated_savings1 = 0
    accumulated_savings2 = 0

    for m1, m2 in zip(parent1, parent2):
        point = random.randint(0, len(m1))
        c1 = m1[:point] + m2[point:]
        c2 = m2[:point] + m1[point:]
        if accumulated_savings1 >= goals[0]["amount"]:
            c1[savings_idx] = 0
        if accumulated_savings2 >= goals[0]["amount"]:
            c2[savings_idx] = 0
        child1.append(c1)
        child2.append(c2)
        accumulated_savings1 += c1[savings_idx]
        accumulated_savings2 += c2[savings_idx]

    return child1, child2


def mutate(solution, categories, income, debts, goals):
    """
    Мутация с учётом цели.
    - Сбережения: ±5% от 25 000 до цели, затем 0.
    - Нерегулярные траты: до 30% после цели.
    """
    temp_debts = [{"remaining": d["remaining"], "payment": d["payment"], "rate": d["rate"]} for d in debts]
    savings_idx = next(i for i, cat in enumerate(categories) if cat["name"] == "Сбережения")
    accumulated_savings = 0
    min_fixed = sum(cat["fixed"] for cat in categories if cat["fixed"] is not None and cat["active"])
    min_regular = sum(cat["min"] for cat in categories if cat["regular"] is not None and cat["active"])

    for month_idx in range(len(solution)):
        debt_payment = sum(d["payment"] for d in temp_debts if d["remaining"] > 0)
        available_income = income - debt_payment - min_fixed

        # Обнуление сбережений
        if accumulated_savings >= goals[0]["amount"]:
            solution[month_idx][savings_idx] = 0
        target_savings = (income * 0.1) if any(d["remaining"] > 0 for d in temp_debts) else \
                         (goals[0]["amount"] / goals[0]["term"] if goals and accumulated_savings < goals[0]["amount"] else 0)

        # Мутация
        idx = random.randint(0, len(solution[month_idx]) - 1)
        cat = categories[idx]
        if cat["fixed"] is None and cat["active"]:
            remaining = available_income - sum(
                s for i, s in enumerate(solution[month_idx]) if i != idx and categories[i]["fixed"] is None)
            min_val = cat["min"]
            if cat["name"] == "Сбережения" and accumulated_savings < goals[0]["amount"]:
                max_val = target_savings * 1.05
                min_val = max(min_val, target_savings * 0.95)
                solution[month_idx][idx] = min(solution[month_idx][idx], max_val)
            elif cat["regular"] is not None:
                max_val = cat["regular"] * 1.1
                min_val = cat["regular"] * 0.9
            elif cat["type"] == "irregular":
                max_val = min(remaining, income * 0.3 if accumulated_savings >= goals[0]["amount"] else income * 0.1)
                if random.random() < min(1.0, cat["irregular_freq"] * 2):
                    solution[month_idx][idx] = random.uniform(min_val, max_val) if max_val > min_val else min_val
                else:
                    solution[month_idx][idx] = 0
            else:
                max_val = remaining / 2
            solution[month_idx][idx] = max(min_val, random.uniform(min_val, max_val)) if max_val > min_val else min_val

        # Проверка бюджета
        total = sum(solution[month_idx]) + debt_payment
        if total > income:
            scale = (income - debt_payment - min_fixed) / sum(
                s for i, s in enumerate(solution[month_idx]) if categories[i]["fixed"] is None)
            for i, cat in enumerate(categories):
                if cat["fixed"] is None and cat["active"]:
                    solution[month_idx][i] = max(cat["min"], solution[month_idx][i] * scale)

        # Обновление долгов
        for d in temp_debts:
            if d["remaining"] > 0:
                interest = d["remaining"] * (d["rate"] / 12)
                principal = d["payment"] - interest
                d["remaining"] = max(0, d["remaining"] - principal)
                if d["remaining"] <= 0:
                    d["payment"] = 0

        accumulated_savings += solution[month_idx][savings_idx]

    return solution


def optimize_budget(income, categories, debts, goals, months=1, weights=(0.4, 0.3, 0.3)):
    """
    Оптимизирует бюджет с помощью ГА.
    """
    def initialize_population(pop_size):
        population = []
        fixed_total = sum(cat["fixed"] for cat in categories if cat["fixed"] is not None and cat["active"])
        min_regular = sum(cat["min"] for cat in categories if cat["regular"] is not None and cat["active"])
        savings_idx = next(i for i, cat in enumerate(categories) if cat["name"] == "Сбережения")

        for _ in range(pop_size):
            solution = []
            temp_debts = [{"remaining": d["remaining"], "payment": d["payment"], "rate": d["rate"]} for d in debts]
            accumulated_savings = 0
            for _ in range(months):
                month_solution = [0] * len(categories)
                debt_payment = sum(d["payment"] for d in temp_debts if d["remaining"] > 0)
                available_income = income - debt_payment - fixed_total

                # Обнуление сбережений
                if accumulated_savings >= goals[0]["amount"]:
                    month_solution[savings_idx] = 0
                    target_savings = 0
                else:
                    target_savings = (income * 0.1) if any(d["remaining"] > 0 for d in temp_debts) else \
                                     (goals[0]["amount"] / goals[0]["term"] if goals else income * 0.2)
                    target_savings = max(0, min(target_savings, available_income - min_regular))

                # Инициализация
                for i, cat in enumerate(categories):
                    if not cat["active"]:
                        month_solution[i] = 0
                    elif cat["fixed"] is not None:
                        month_solution[i] = cat["fixed"]
                    elif cat["name"] == "Сбережения" and accumulated_savings < goals[0]["amount"]:
                        month_solution[i] = random.uniform(target_savings * 0.95, target_savings * 1.05)
                    elif cat["regular"] is not None:
                        month_solution[i] = random.uniform(cat["regular"] * 0.9, cat["regular"] * 1.1)
                    elif cat["type"] == "irregular" and random.random() < min(1.0, cat["irregular_freq"] * 2):
                        min_spend = cat["min"]
                        max_spend = min(available_income, income * 0.3 if accumulated_savings >= goals[0]["amount"] else income * 0.1)
                        month_solution[i] = random.uniform(min_spend, max_spend) if max_spend > min_spend else min_spend

                # Проверка бюджета
                total = sum(month_solution) + debt_payment
                if total > income:
                    scale = (income - debt_payment - fixed_total) / sum(
                        s for i, s in enumerate(month_solution) if categories[i]["fixed"] is None)
                    for i, cat in enumerate(categories):
                        if cat["fixed"] is None and cat["active"]:
                            month_solution[i] = max(cat["min"], month_solution[i] * scale)

                solution.append(month_solution)
                accumulated_savings += month_solution[savings_idx]

                # Обновление долгов
                for d in temp_debts:
                    if d["remaining"] > 0:
                        interest = d["remaining"] * (d["rate"] / 12)
                        principal = d["payment"] - interest
                        d["remaining"] = max(0, d["remaining"] - principal)
                        if d["remaining"] <= 0:
                            d["payment"] = 0

            population.append(solution)
        return population

    pop_size = 100
    generations = 1000
    history = load_budget_history()
    population = initialize_population(pop_size)
    threshold = 10.0  # Порог для ранней остановки
    for gen in range(generations):
        fitness_scores = [fitness(ind, categories, income, debts, goals, history, weights) for ind in population]
        max_fitness_idx = fitness_scores.index(max(fitness_scores))
        if fitness_scores[max_fitness_idx] > threshold:
            break
        parents = select_parents(population, fitness_scores)
        offspring = []
        for i in range(0, len(parents), 2):
            if i + 1 < len(parents):
                child1, child2 = crossover(parents[i], parents[i + 1], categories, goals)
                offspring.append(mutate(child1, categories, income, debts, goals))
                offspring.append(mutate(child2, categories, income, debts, goals))
        population = parents + offspring[:pop_size - len(parents)]

    best_solution = max(population, key=lambda x: fitness(x, categories, income, debts, goals, history, weights))
    return best_solution, debts