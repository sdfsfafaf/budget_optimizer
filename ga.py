# ga.py
import random
import numpy as np


def generate_individual(income, categories, min_savings, strategy="max_savings"):
    individual = [0] * len(categories)
    fixed_total = sum(cat["fixed"] or 0 for cat in categories if cat["active"] and cat["fixed"])
    remaining = income - fixed_total

    # Устанавливаем фиксированные суммы
    for i, cat in enumerate(categories):
        if cat["active"] and cat["fixed"]:
            individual[i] = cat["fixed"]

    # Устанавливаем минимальные суммы для переменных категорий
    variable_cats = [i for i, cat in enumerate(categories) if cat["active"] and not cat["fixed"]]
    total_min = sum(categories[i]["min"] for i in variable_cats)
    for i in variable_cats:
        individual[i] = categories[i]["min"]
    remaining -= total_min

    if remaining < 0:
        scale = (income - fixed_total) / total_min if total_min > 0 else 0
        for i in variable_cats:
            individual[i] = categories[i]["min"] * scale
        remaining = 0

    if remaining > 0:
        savings_idx = next(i for i, cat in enumerate(categories) if cat["name"] == "Сбережения" and cat["active"])
        is_savings_fixed = categories[savings_idx]["fixed"] is not None
        other_variable_cats = [i for i in variable_cats if i != savings_idx] if not is_savings_fixed else variable_cats

        if strategy == "max_savings" and not is_savings_fixed:
            individual[savings_idx] = individual[savings_idx] + remaining  # Добавляем весь остаток в сбережения
        else:  # balance
            savings_min = categories[savings_idx]["min"]
            individual[savings_idx] = savings_min
            remaining -= savings_min
            if remaining > 0 and other_variable_cats:
                weights = [categories[i]["weight"] for i in other_variable_cats]
                total_weight = sum(weights)
                for i, w in zip(other_variable_cats, weights):
                    share = (w / total_weight) * remaining
                    individual[i] += share

    return individual


def fitness(individual, categories, income, min_savings, history=None, strategy="max_savings"):
    savings_idx = next(i for i, cat in enumerate(categories) if cat["name"] == "Сбережения" and cat["active"])
    savings = individual[savings_idx]
    is_savings_fixed = categories[savings_idx]["fixed"] is not None

    savings_score = min(savings / min_savings, 1.0) if min_savings > 0 and not is_savings_fixed else 1.0
    total_weight = sum(cat["weight"] for cat in categories if cat["active"] and not cat["fixed"])
    balance_score = 0
    if total_weight > 0:
        balance_score = sum((individual[i] - cat["min"]) * (cat["weight"] / total_weight)
                            for i, cat in enumerate(categories) if cat["active"] and not cat["fixed"]) / income

    comfort_score = 0
    variable_cats = [i for i, cat in enumerate(categories) if cat["active"] and not cat["fixed"] and cat["name"] != "Сбережения"]
    if variable_cats:
        avg_spend = (income - sum(cat["fixed"] or 0 for cat in categories if cat["active"])) / len(variable_cats)
        for i in variable_cats:
            diff = (individual[i] - avg_spend) / avg_spend if avg_spend > 0 else 0
            comfort_score += 1 - diff ** 2
        comfort_score /= len(variable_cats)

    history_score = 1.0
    if history:
        total_deviation = 0
        count = 0
        for i, cat in enumerate(categories):
            if cat["active"] and not cat["fixed"] and cat["name"] in history:
                expected = history[cat["name"]]
                actual = individual[i]
                total_deviation += abs(expected - actual) / expected if expected > 0 else 0
                count += 1
        history_score = 1.0 - (total_deviation / count) if count > 0 else 1.0
        history_score = max(0, history_score)

    if strategy == "max_savings":
        return 0.5 * savings_score + 0.2 * balance_score + 0.2 * comfort_score + 0.1 * history_score
    else:
        return 0.3 * savings_score + 0.3 * balance_score + 0.3 * comfort_score + 0.1 * history_score


def crossover(parent1, parent2, categories):
    child = parent1.copy()
    variable_cats = [i for i, cat in enumerate(categories) if cat["active"] and not cat["fixed"]]
    if len(variable_cats) > 1:
        crossover_points = random.sample(variable_cats, min(2, len(variable_cats)))
        for i in variable_cats:
            if i in crossover_points:
                child[i] = parent2[i]
    total = sum(child)
    income = sum(parent1)
    if total != income and variable_cats:
        adjustment = income - total
        if adjustment > 0:
            child[variable_cats[0]] += adjustment
        elif adjustment < 0:
            for i in variable_cats:
                if child[i] > categories[i]["min"]:
                    reducible = child[i] - categories[i]["min"]
                    reduction = min(-adjustment, reducible)
                    child[i] -= reduction
                    adjustment += reduction
                    if adjustment == 0:
                        break
    return child


def mutate(individual, categories, income, mutation_rate=0.3):
    if random.random() < mutation_rate:
        variable_cats = [i for i, cat in enumerate(categories) if cat["active"] and not cat["fixed"]]
        if len(variable_cats) > 1:
            i1, i2 = random.sample(variable_cats, 2)
            max_amount = min(individual[i1] - categories[i1]["min"], income * 0.1)
            amount = random.uniform(-max_amount, max_amount)
            if individual[i1] + amount >= categories[i1]["min"] and individual[i2] - amount >= categories[i2]["min"]:
                individual[i1] += amount
                individual[i2] -= amount
    return individual


def optimize_budget(income, categories, min_savings, history=None, strategy="max_savings", population_size=100, generations=100):
    population = [generate_individual(income, categories, min_savings, strategy) for _ in range(population_size)]

    for generation in range(generations):
        fitness_scores = [fitness(ind, categories, income, min_savings, history, strategy) for ind in population]
        sorted_pairs = sorted(zip(fitness_scores, population), reverse=True)
        top_half = [ind for _, ind in sorted_pairs[:population_size // 2]]

        next_population = top_half.copy()
        while len(next_population) < population_size:
            parent1, parent2 = random.sample(top_half, 2)
            child = crossover(parent1, parent2, categories)
            child = mutate(child, categories, income, mutation_rate=0.3 if generation < generations // 2 else 0.1)
            next_population.append(child)

        population = next_population[:population_size]

    fitness_scores = [fitness(ind, categories, income, min_savings, history, strategy) for ind in population]
    best_individual = population[np.argmax(fitness_scores)]
    return best_individual