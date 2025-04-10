import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from data import load_categories, save_categories, load_goals, save_goals, calculate_annuity_payment
from history import load_income_history, save_budget_to_history
from ga import optimize_budget

def simulate_period(income, categories, debts):
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
    solution, updated_debts = optimize_budget(income, categories, debts_list, goals, months=num_months)

    for month in range(num_months):
        current_month = (datetime.now() + timedelta(days=30 * month)).strftime("%Y-%m")
        month_solution = solution[month].copy()
        total_debt_payment = sum(d["payment"] for d in updated_debts if d["remaining"] > 0)
        available_income = income - total_debt_payment
        total_fixed = sum(cat["fixed"] for cat in categories if cat["fixed"] and cat["active"])
        total_min = sum(cat["min"] for cat in categories if not cat["fixed"] and cat["active"])

        # Корректировка расходов до добавления долгов
        total_spend = sum(month_solution)
        if total_spend > available_income:
            non_fixed_total = sum(s for i, s in enumerate(month_solution) if not categories[i]["fixed"])
            if non_fixed_total > 0:
                scale = (available_income - total_fixed) / non_fixed_total
                for i in range(len(month_solution)):
                    if not categories[i]["fixed"]:
                        month_solution[i] = max(categories[i]["min"], month_solution[i] * scale)
            total_spend = sum(month_solution)

        # Досрочное погашение долгов
        remaining_income = available_income - total_spend
        if remaining_income > 0:
            sorted_debts = sorted([d for d in updated_debts if d["remaining"] > 0], key=lambda x: x["rate"], reverse=True)
            for d in sorted_debts:
                if remaining_income > 0:
                    extra_payment = min(remaining_income, d["remaining"] - d["payment"])
                    if extra_payment > 0:
                        d["remaining"] -= extra_payment
                        total_debt_payment += extra_payment
                        remaining_income -= extra_payment
                        if d["remaining"] <= 0:
                            d["payment"] = 0

        # Строгая финальная корректировка
        total_spend_with_debts = sum(month_solution) + total_debt_payment
        if total_spend_with_debts > income:
            excess = total_spend_with_debts - income
            savings = month_solution[savings_idx]
            if savings > excess:
                month_solution[savings_idx] -= excess
            else:
                month_solution[savings_idx] = 0
                remaining_excess = excess - savings
                non_fixed_total = sum(s for i, s in enumerate(month_solution) if not categories[i]["fixed"] and i != savings_idx)
                if non_fixed_total > 0:
                    scale = (income - total_debt_payment - total_fixed - month_solution[savings_idx]) / non_fixed_total
                    for i in range(len(month_solution)):
                        if not categories[i]["fixed"] and i != savings_idx:
                            month_solution[i] = max(categories[i]["min"], month_solution[i] * scale)
            total_spend_with_debts = sum(month_solution) + total_debt_payment

        # Вывод
        print(f"\nМесяц {month + 1} ({current_month}):")
        for i, cat in enumerate(categories):
            if cat["active"] and month_solution[i] > 0:
                print(f"{cat['name']}: {month_solution[i]:.2f} руб.")
        print(f"Долги: {total_debt_payment:.2f} руб.")
        print(f"Общая сумма: {total_spend_with_debts:.2f} руб.")

        total_savings += month_solution[savings_idx]
        save_budget_to_history(current_month, income, month_solution, total_debt_payment)
        results.append((current_month, month_solution, total_debt_payment))

        # Обновление долгов
        for d in updated_debts:
            if d["remaining"] > 0:
                interest = d["remaining"] * (d["rate"] / 12)
                principal = min(d["payment"], d["remaining"] + interest) - interest
                d["remaining"] = max(0, d["remaining"] - principal)
                if d["remaining"] <= 0:
                    d["payment"] = 0

    # Вывод итогов и график
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

    plt.figure(figsize=(10, 6))
    plt.plot(dates, savings, label="Сбережения")
    plt.plot(dates, debt_payments, label="Платежи по долгам")
    plt.xlabel("Месяц")
    plt.ylabel("Сумма (руб.)")
    plt.title("Динамика сбережений и долгов")
    plt.legend()
    plt.grid(True)
    plt.show()

def main():
    income_history = load_income_history()
    fill_history = input("Хотите заполнить историю? (да/нет)\n")
    if fill_history.lower() == "да":
        income_history = load_income_history()  # Повторная загрузка после заполнения

    current_month = datetime.now().strftime("%Y-%m")
    income = income_history.get(current_month, 100000.0)
    print(f"Доход за {current_month}: {income} руб. Хотите обновить? (да/нет)")
    if input().lower() == "да":
        income = float(input("Введите новый доход: "))

    categories = load_categories()
    print("\nТекущие категории:")
    for i, cat in enumerate(categories):
        print(f"{i + 1}. {cat['name']} (fixed: {cat['fixed']}, min: {cat['min']}, weight: {cat['weight']}, active: {cat['active']})")

    while True:
        print("\n1. Добавить категорию\n2. Удалить категорию\n3. Изменить категорию\n4. Завершить")
        choice = input("Выберите действие: ")
        if choice == "1":
            name = input("Название категории: ")
            fixed = input("Фиксированная сумма (или Enter для переменной): ")
            fixed = float(fixed) if fixed else None
            min_cost = float(input("Минимальная сумма: "))
            weight = float(input("Вес (1–10): "))
            categories.append({"name": name, "fixed": fixed, "min": min_cost, "weight": weight, "active": 1})
        elif choice == "2":
            idx = int(input("Номер категории для удаления: ")) - 1
            if 0 <= idx < len(categories):
                categories.pop(idx)
        elif choice == "3":
            idx = int(input("Номер категории для изменения: ")) - 1
            if 0 <= idx < len(categories):
                field = input("Что изменить (name/fixed/min/weight/active)? ")
                if field in categories[idx]:
                    if field == "fixed":
                        value = input("Новое значение (или Enter для None): ")
                        categories[idx][field] = float(value) if value else None
                    elif field == "active":
                        categories[idx][field] = int(input("Новое значение (0/1): "))
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

    simulate_period(income, categories, debts)

if __name__ == "__main__":
    main()
