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


def fitness(solution, categories, income, debts, goals, history, weights=(0.4, 0.3, 0.3)):
    savings_total = 0
    accumulated_savings = 0
    temp_debts = [{"remaining": d["remaining"], "payment": d["payment"], "rate": d["rate"]} for d in debts]
    savings_idx = next(i for i, cat in enumerate(categories) if cat["name"] == "Сбережения")

    balance_score = 0
    fixed_penalty = 0
    regular_variance_penalty = 0
    irregular_score = 0
    goal_score = 0
    savings_list = []
    debt_payments = []

    category_variance_penalty = 0
    savings_debt_balance_penalty = 0

    min_fixed = sum(cat["fixed"] for cat in categories if cat["fixed"] is not None and cat["active"])
    active_cats = [(i, cat) for i, cat in enumerate(categories) if cat["active"]]
    category_expenses = {i: [] for i, _ in active_cats}

    for month_idx in range(len(solution)):
        savings = solution[month_idx][savings_idx]
        savings_total += savings
        accumulated_savings += savings
        savings_list.append(savings)

        for i, cat in active_cats:
            category_expenses[i].append(solution[month_idx][i])
            if cat["fixed"] is not None and solution[month_idx][i] != cat["fixed"]:
                fixed_penalty += abs(solution[month_idx][i] - cat["fixed"]) / income
            elif cat["regular"] is not None:
                avg_regular = cat["regular"]
                if abs(solution[month_idx][i] - avg_regular) > avg_regular * 0.1:
                    regular_variance_penalty += abs(solution[month_idx][i] - avg_regular) / income
            elif cat["type"] == "irregular" and solution[month_idx][i] > income * 0.05:
                balance_score += (solution[month_idx][i] - income * 0.05) / income

        if accumulated_savings >= goals[0]["amount"] and all(d["remaining"] <= 0 for d in temp_debts):
            irregular_score += 2 * sum(
                solution[month_idx][i] for i, cat in active_cats if cat["type"] == "irregular") / (income * 0.4)

        debt_payment = sum(d["payment"] for d in temp_debts if d["remaining"] > 0)
        debt_payments.append(debt_payment)
        total_spend = sum(solution[month_idx]) + debt_payment
        if total_spend > income:
            balance_score += (total_spend - income) / income

        for d in temp_debts:
            if d["remaining"] > 0:
                interest = d["remaining"] * (d["rate"] / 12)
                principal = d["payment"] - interest
                d["remaining"] = max(0, d["remaining"] - principal)

    for i, expenses in category_expenses.items():
        if len(expenses) > 1 and sum(expenses) > 0:
            avg_expense = sum(expenses) / len(expenses)
            variance = sum(abs(exp - avg_expense) for exp in expenses) / len(expenses)
            category_variance_penalty += variance / income

    # Штраф за неравномерность суммы сбережений и долгов
    debt_savings_sum = [s + d for s, d in zip(savings_list, debt_payments)]
    if debt_savings_sum and sum(debt_savings_sum) > 0:
        avg_debt_savings = sum(debt_savings_sum) / len(debt_savings_sum)
        debt_savings_variance = sum(abs(ds - avg_debt_savings) for ds in debt_savings_sum) / len(debt_savings_sum)
        savings_debt_balance_penalty = 4 * debt_savings_variance / income  # Увеличен коэффициент с 2 до 4

    if goals:
        goal_progress = min(1, accumulated_savings / goals[0]["amount"])
        if accumulated_savings > goals[0]["amount"]:
            goal_score -= 5000 * (accumulated_savings - goals[0]["amount"]) / income
        goal_score += goal_progress
    else:
        goal_score = 1

    savings_score = savings_total / income if accumulated_savings < goals[0]["amount"] else 0
    balance_penalty = 1 / (1 + balance_score)
    fixed_penalty_factor = 1 / (1 + fixed_penalty)
    regular_penalty_factor = 1 / (1 + regular_variance_penalty)
    category_penalty_factor = 1 / (1 + category_variance_penalty)
    savings_debt_penalty_factor = 1 / (1 + savings_debt_balance_penalty)

    total_fitness = (
        weights[0] * savings_score +
        weights[1] * goal_score +
        weights[2] * irregular_score
    ) * balance_penalty * fixed_penalty_factor * regular_penalty_factor * category_penalty_factor * savings_debt_penalty_factor

    return total_fitness


def crossover(parent1, parent2, categories, goals):
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
    temp_debts = [{"remaining": d["remaining"], "payment": d["payment"], "rate": d["rate"]} for d in debts]
    savings_idx = next(i for i, cat in enumerate(categories) if cat["name"] == "Сбережения")
    accumulated_savings = 0
    min_fixed = sum(cat["fixed"] for cat in categories if cat["fixed"] is not None and cat["active"])
    active_indices = [i for i, cat in enumerate(categories) if cat["fixed"] is None and cat["active"]]

    for month_idx in range(len(solution)):
        debt_payment = sum(d["payment"] for d in temp_debts if d["remaining"] > 0)
        available_income = income - debt_payment - min_fixed

        target_savings = goals[0]["amount"] / goals[0]["term"] if goals and accumulated_savings < goals[0][
            "amount"] else 0

        if active_indices and random.random() < 0.5:
            idx = random.choice(active_indices)
            cat = categories[idx]
            remaining = available_income - sum(
                s for i, s in enumerate(solution[month_idx]) if i != idx and categories[i]["fixed"] is None)
            min_val = cat["min"]
            if cat["name"] == "Сбережения" and accumulated_savings < goals[0]["amount"]:
                # Изменение: Минимальное значение сбережений ближе к целевому
                solution[month_idx][idx] = random.uniform(max(target_savings * 0.9, min_val), target_savings * 1.1)
            elif cat["regular"] is not None:
                max_val = cat["regular"] * 1.1
                min_val = cat["regular"] * 0.9
                solution[month_idx][idx] = random.uniform(min_val, max_val) if max_val > min_val else min_val
            elif cat["type"] == "irregular":
                max_val = min(remaining, income * 0.4)
                if random.random() < min(1.0, cat["irregular_freq"] * 4):
                    solution[month_idx][idx] = random.uniform(min_val, max_val) if max_val > min_val else min_val
                else:
                    solution[month_idx][idx] = min_val  # Изменение: Минимальное значение для нерегулярных
            solution[month_idx][idx] = max(min_val, solution[month_idx][
                idx]) if "max_val" in locals() and max_val > min_val else min_val

        total = sum(solution[month_idx]) + debt_payment
        if total > income:
            scale = (income - debt_payment - min_fixed) / sum(
                s for i, s in enumerate(solution[month_idx]) if categories[i]["fixed"] is None)
            for i, cat in enumerate(categories):
                if cat["fixed"] is None and cat["active"]:
                    solution[month_idx][i] = max(cat["min"], solution[month_idx][i] * scale)

        for d in temp_debts:
            if d["remaining"] > 0:
                interest = d["remaining"] * (d["rate"] / 12)
                principal = d["payment"] - interest
                d["remaining"] = max(0, d["remaining"] - principal)

        accumulated_savings += solution[month_idx][savings_idx]

    return solution


def optimize_budget(income, categories, debts, goals, months=1, weights=(0.4, 0.3, 0.3)):
    def initialize_population(pop_size):
        population = []
        fixed_total = sum(cat["fixed"] for cat in categories if cat["fixed"] is not None and cat["active"])
        savings_idx = next(i for i, cat in enumerate(categories) if cat["name"] == "Сбережения")

        for _ in range(pop_size):
            solution = []
            temp_debts = [{"remaining": d["remaining"], "payment": d["payment"], "rate": d["rate"]} for d in debts]
            accumulated_savings = 0
            for _ in range(months):
                month_solution = [0] * len(categories)
                debt_payment = sum(d["payment"] for d in temp_debts if d["remaining"] > 0)
                available_income = income - debt_payment - fixed_total

                target_savings = goals[0]["amount"] / goals[0]["term"] if goals and accumulated_savings < goals[0][
                    "amount"] else 0

                for i, cat in enumerate(categories):
                    if not cat["active"]:
                        month_solution[i] = 0
                    elif cat["fixed"] is not None:
                        month_solution[i] = cat["fixed"]
                    elif cat["name"] == "Сбережения" and accumulated_savings < goals[0]["amount"]:
                        # Изменение: Минимальное значение сбережений ближе к целевому
                        month_solution[i] = random.uniform(max(target_savings * 0.9, cat["min"]), target_savings * 1.1)
                    elif cat["regular"] is not None:
                        month_solution[i] = random.uniform(cat["regular"] * 0.9, cat["regular"] * 1.1)
                    elif cat["type"] == "irregular" and random.random() < min(1.0, cat["irregular_freq"] * 4):
                        min_spend = cat["min"]
                        max_spend = min(available_income, income * 0.4)
                        month_solution[i] = random.uniform(min_spend, max_spend) if max_spend > min_spend else min_spend
                    else:
                        month_solution[i] = cat["min"]  # Изменение: Минимальное значение для нерегулярных

                total = sum(month_solution) + debt_payment
                if total > income:
                    scale = (income - debt_payment - fixed_total) / sum(
                        s for i, s in enumerate(month_solution) if categories[i]["fixed"] is None)
                    for i, cat in enumerate(categories):
                        if cat["fixed"] is None and cat["active"]:
                            month_solution[i] = max(cat["min"], month_solution[i] * scale)

                solution.append(month_solution)
                accumulated_savings += month_solution[savings_idx]

                for d in temp_debts:
                    if d["remaining"] > 0:
                        interest = d["remaining"] * (d["rate"] / 12)
                        principal = d["payment"] - interest
                        d["remaining"] = max(0, d["remaining"] - principal)

            population.append(solution)
        return population

    pop_size = 30
    generations = 300
    history = load_budget_history()
    population = initialize_population(pop_size)
    threshold = 15.0
    best_fitness = -float('inf')
    stagnation = 0

    for gen in range(generations):
        fitness_scores = [fitness(ind, categories, income, debts, goals, history, weights) for ind in population]
        max_fitness_idx = fitness_scores.index(max(fitness_scores))
        if fitness_scores[max_fitness_idx] > threshold:
            break
        if abs(fitness_scores[max_fitness_idx] - best_fitness) < 1e-4:
            stagnation += 1
        else:
            stagnation = 0
            best_fitness = fitness_scores[max_fitness_idx]
        if stagnation > 30:
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