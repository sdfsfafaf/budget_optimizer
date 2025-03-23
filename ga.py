import random
import numpy as np

def optimize_budget(income, categories, min_savings, debt_payment=None, strategy="max_savings"):
    if debt_payment is None:
        debt_payment = 0
    total_budget = income - debt_payment

    def generate_solution():
        solution = []
        remaining_budget = total_budget
        for cat in categories:
            if not cat["active"]:
                solution.append(0)
            elif cat["fixed"]:
                solution.append(cat["fixed"])
                remaining_budget -= cat["fixed"]
            else:
                solution.append(cat["min"])
                remaining_budget -= cat["min"]
        return solution, remaining_budget

    def fitness(solution):
        total = sum(solution)
        if total > total_budget:
            return -float("inf")
        return sum(cat["weight"] * val for cat, val in zip(categories, solution) if cat["active"])

    population_size = 100
    generations = 200
    mutation_rate = 0.1

    initial_solution, remaining_budget = generate_solution()
    population = [initial_solution[:] for _ in range(population_size)]

    savings_idx = next(i for i, cat in enumerate(categories) if cat["name"] == "Сбережения")
    variable_indices = [i for i, cat in enumerate(categories) if cat["active"] and not cat["fixed"] and i != savings_idx]

    for _ in range(population_size):
        for i in variable_indices:
            population[_][i] += random.uniform(0, remaining_budget / len(variable_indices))
        population[_][savings_idx] = max(0, total_budget - sum(population[_][i] for i in range(len(categories)) if i != savings_idx))

    for _ in range(generations):
        new_population = []
        for _ in range(population_size // 2):
            parent1 = max(random.sample(population, 3), key=fitness)
            parent2 = max(random.sample(population, 3), key=fitness)
            child1, child2 = parent1[:], parent2[:]
            for i in variable_indices:
                if random.random() < 0.5:
                    child1[i], child2[i] = child2[i], child1[i]
            for child in [child1, child2]:
                for i in variable_indices:
                    if random.random() < mutation_rate:
                        child[i] = max(categories[i]["min"], child[i] + random.uniform(-remaining_budget * 0.1, remaining_budget * 0.1))
                child[savings_idx] = max(0, total_budget - sum(child[i] for i in range(len(categories)) if i != savings_idx))
                new_population.append(child)
        population = new_population

    best_solution = max(population, key=fitness)

    if strategy == "balance":
        best_solution[savings_idx] = min(categories[savings_idx]["min"], total_budget - sum(best_solution[i] for i in range(len(categories)) if i != savings_idx))
        remaining_budget = total_budget - sum(best_solution[i] for i in range(len(categories)))
        if remaining_budget > 0:
            weights = [cat["weight"] for i, cat in enumerate(categories) if i in variable_indices]
            total_weight = sum(weights)
            for i, idx in enumerate(variable_indices):
                best_solution[idx] += min((remaining_budget * weights[i] / total_weight), total_budget - sum(best_solution))
        # Нормализация, чтобы не превышать total_budget
        total = sum(best_solution)
        if total > total_budget:
            scale = total_budget / total
            best_solution = [val * scale for val in best_solution]

    return [max(0, val) for val in best_solution]
