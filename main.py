import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from data import load_categories, save_categories, load_goals, save_goals, calculate_annuity_payment
from history import load_income_history, save_budget_to_history
from ga import optimize_budget

def simulate_period(income, categories, debts, weights=(0.5, 0.3, 0.2)):
    num_months = int(input("Введите количество месяцев для расчёта бюджета (например, 6): "))
    goals = load_goals()
    results = []
    debt_history = {debt["name"]: {"remaining": debt["amount"],
                                   "payment": calculate_annuity_payment(debt["amount"], debt["term"], debt["rate"]),
                                   "term": debt["term"],
                                   "rate": debt["rate"]}
                    for debt in debts}
    savings_idx = next(i for i, cat in enumerate(categories) if cat["name"] == "Сбережения")
    total_savings = 0

    debts_list = list(debt_history.values())
    solution, updated_debts = optimize_budget(income, categories, debts_list, goals, months=num_months, weights=weights)

    for month in range(num_months):
        current_month = (datetime.now() + timedelta(days=30 * month)).strftime("%Y-%m")
        month_solution = solution[month].copy()
        total_debt_payment = sum(d["payment"] for d in updated_debts if d["remaining"] > 0)
        available_income = income - total_debt_payment

        total_fixed = sum(cat["fixed"] for cat in categories if cat["fixed"] is not None and cat["active"])
        total_regular = sum(cat["regular"] for cat in categories if cat["regular"] is not None and cat["active"]) or 0
        total_mandatory_irregular = 0

        for i, cat in enumerate(categories):
            if cat["type"] == "irregular" and cat["mandatory"] and cat["active"] and month_solution[i] > 0:
                total_mandatory_irregular += month_solution[i]

        total_spend = sum(month_solution)
        if total_spend > available_income:
            non_mandatory_irregular_total = sum(s for i, s in enumerate(month_solution)
                                                if categories[i]["type"] == "irregular" and not categories[i]["mandatory"] and categories[i]["active"])
            if non_mandatory_irregular_total > 0 and total_spend - total_fixed - total_regular - total_mandatory_irregular > available_income:
                scale = (available_income - total_fixed - total_regular - total_mandatory_irregular) / non_mandatory_irregular_total
                for i, cat in enumerate(categories):
                    if cat["type"] == "irregular" and not cat["mandatory"] and cat["active"]:
                        month_solution[i] = max(0, month_solution[i] * scale)
            regular_total = sum(s for i, s in enumerate(month_solution) if categories[i]["regular"] is not None and categories[i]["active"])
            if regular_total > 0 and total_spend > available_income:
                scale = (available_income - total_fixed - total_mandatory_irregular) / regular_total
                for i, cat in enumerate(categories):
                    if cat["regular"] is not None and cat["active"]:
                        month_solution[i] = max(cat["min"], month_solution[i] * scale)
            total_spend = sum(month_solution)

        remaining_income = available_income - total_spend
        if remaining_income > 0:
            if any(d["remaining"] > 0 for d in updated_debts):
                sorted_debts = sorted([d for d in updated_debts if d["remaining"] > 0], key=lambda x: x["rate"], reverse=True)
                for d in sorted_debts:
                    if remaining_income > 0:
                        extra_payment = min(remaining_income, d["remaining"])
                        d["remaining"] -= extra_payment
                        total_debt_payment += extra_payment
                        remaining_income -= extra_payment
                        if d["remaining"] <= 0:
                            d["payment"] = 0
            else:
                month_solution[savings_idx] += remaining_income

        total_spend_with_debts = sum(month_solution) + total_debt_payment
        if total_spend_with_debts > income:
            excess = total_spend_with_debts - income
            savings = month_solution[savings_idx]
            if savings >= excess:
                month_solution[savings_idx] -= excess
            else:
                month_solution[savings_idx] = 0
                remaining_excess = excess - savings
                non_mandatory_total = sum(s for i, s in enumerate(month_solution)
                                          if categories[i]["type"] == "irregular" and not categories[i]["mandatory"] and categories[i]["active"])
                if non_mandatory_total > 0:
                    scale = (income - total_debt_payment - total_fixed - total_regular - total_mandatory_irregular) / non_mandatory_total
                    for i, cat in enumerate(categories):
                        if cat["type"] == "irregular" and not cat["mandatory"] and cat["active"]:
                            month_solution[i] = max(0, month_solution[i] * scale)

        print(f"\nМесяц {month + 1} ({current_month}):")
        for i, cat in enumerate(categories):
            if cat["active"] and month_solution[i] > 0:
                print(f"{cat['name']}: {month_solution[i]:.2f} руб.")
        print(f"Долги: {total_debt_payment:.2f} руб.")
        print(f"Общая сумма: {total_spend_with_debts:.2f} руб.")

        total_savings += month_solution[savings_idx]
        save_budget_to_history(current_month, income, month_solution, total_debt_payment)
        results.append((current_month, month_solution, total_debt_payment))

        for d in updated_debts:
            if d["remaining"] > 0:
                interest = d["remaining"] * (d["rate"] / 12)
                principal = min(d["payment"], d["remaining"] + interest) - interest
                d["remaining"] = max(0, d["remaining"] - principal)
                if d["remaining"] <= 0:
                    d["payment"] = 0

    if goals:
        print(f"\nИтоговые сбережения за {num_months} мес.: {total_savings:.2f} руб.")
        seen_goals = set()
        for goal in goals:
            if goal["name"] not in seen_goals:
                months_needed = goal["amount"] / total_savings * num_months if total_savings > 0 else float("inf")
                print(f"Цель '{goal['name']}': {goal['amount']} руб. достигнута через {months_needed:.1f} мес.")
                seen_goals.add(goal["name"])

    dates = [res[0] for res in results]
    savings = [res[1][savings_idx] for res in results]
    debt_payments = [res[2] for res in results]
    total_spends = [sum(res[1]) + res[2] for res in results]

    plt.figure(figsize=(10, 6))
    plt.plot(dates, savings, label="Сбережения")
    plt.plot(dates, debt_payments, label="Платежи по долгам")
    plt.plot(dates, total_spends, label="Суммарные траты")
    plt.xlabel("Месяц")
    plt.ylabel("Сумма (руб.)")
    plt.title("Динамика сбережений, долгов и трат")
    plt.legend()
    plt.grid(True)
    plt.show()

def main():
    income_history = load_income_history()
    fill_history = input("Хотите заполнить историю? (да/нет)\n")
    if fill_history.lower() == "да":
        income_history = load_income_history()

    current_month = datetime.now().strftime("%Y-%m")
    income = income_history.get(current_month, 120000.0)
    print(f"Доход за {current_month}: {income} руб. Хотите обновить? (да/нет)")
    if input().lower() == "да":
        income = float(input("Введите новый доход: "))

    categories = load_categories()
    print("\nТекущие категории:")
    for i, cat in enumerate(categories):
        print(f"{i + 1}. {cat['name']} (type: {cat['type']}, fixed: {cat['fixed']}, regular: {cat['regular']}, "
              f"min: {cat['min']}, weight: {cat['weight']}, mandatory: {cat['mandatory']}, active: {cat['active']}, "
              f"irregular_freq: {cat['irregular_freq']})")

    while True:
        print("\n1. Добавить категорию\n2. Удалить категорию\n3. Изменить категорию\n4. Завершить")
        choice = input("Выберите действие: ")
        if choice == "1":
            name = input("Название категории: ")
            type_choice = input("Тип категории (fixed/regular/irregular): ")
            fixed = None
            regular = None
            min_cost = 0.0
            mandatory = 0
            irregular_freq = 0.0
            if type_choice == "fixed":
                fixed = float(input("Фиксированная сумма: "))
                min_cost = fixed
            elif type_choice == "regular":
                regular = float(input("Средняя сумма: "))
                min_cost = regular * 0.9
            elif type_choice == "irregular":
                min_cost = float(input("Минимальная сумма при трате: "))
                mandatory = int(input("Обязательная? (1 - да, 0 - нет): "))
                irregular_freq = float(input("Частота траты (0.0–1.0): "))
            weight = float(input("Вес (1–10): "))
            categories.append({"name": name, "type": type_choice, "fixed": fixed, "regular": regular, "min": min_cost,
                              "weight": weight, "mandatory": mandatory, "active": 1, "irregular_freq": irregular_freq})
        elif choice == "2":
            idx = int(input("Номер категории для удаления: ")) - 1
            if 0 <= idx < len(categories):
                categories.pop(idx)
        elif choice == "3":
            idx = int(input("Номер категории для изменения: ")) - 1
            if 0 <= idx < len(categories):
                field = input("Что изменить (name/type/fixed/regular/min/weight/mandatory/active/irregular_freq)? ")
                if field in categories[idx]:
                    if field == "fixed" or field == "regular":
                        value = input("Новое значение (или Enter для None): ")
                        categories[idx][field] = float(value) if value else None
                    elif field == "mandatory" or field == "active":
                        categories[idx][field] = int(input("Новое значение (0/1): "))
                    elif field == "type":
                        categories[idx][field] = input("Новый тип (fixed/regular/irregular): ")
                    elif field == "irregular_freq":
                        categories[idx][field] = float(input("Новая частота (0.0–1.0): "))
                    else:
                        categories[idx][field] = float(input("Новое значение: "))
        elif choice == "4":
            break

    save_categories(categories)
    print("\nЗагруженные категории перед оптимизацией:")
    for cat in categories:
        print(cat)

    debts = []
    if input("Хотите ввести свои долги? (да/нет)\n").lower() == "да":
        while True:
            name = input("Введите название долга (или 'стоп' для завершения):\n")
            if name.lower() == "стоп":
                break
            amount = float(input("Общая сумма долга (руб.): "))
            term = int(input("Срок в месяцах: "))
            rate = float(input("Годовая процентная ставка (например, 0.1 для 10%): "))
            debts.append({"name": name, "amount": amount, "term": term, "rate": rate})

    if input("Хотите задать финансовую цель? (да/нет)\n").lower() == "да":
        goal_name = input("Название цели (например, 'Отпуск'): ")
        goal_amount = float(input("Сумма цели (руб.): "))
        goal_term = int(input("Срок в месяцах: "))
        save_goals([{"name": goal_name, "amount": goal_amount, "term": goal_term}])

    print("\nВыберите приоритет оптимизации:")
    print("1. Максимизировать сбережения\n2. Погасить долги\n3. Сбалансированный бюджет")
    choice = input("Ваш выбор (1-3): ")
    weights = {
        "1": (0.7, 0.2, 0.1),
        "2": (0.2, 0.7, 0.1),
        "3": (0.4, 0.3, 0.3)
    }.get(choice, (0.4, 0.3, 0.3))

    simulate_period(income, categories, debts, weights)

if __name__ == "__main__":
    main()