import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from data import load_categories, save_categories, load_goals, save_goals, calculate_annuity_payment
from history import load_income_history, update_debt_after_payment, save_budget_to_history
from ga import optimize_budget

def simulate_period(income, categories, debts):
    num_months = int(input("Введите количество месяцев для расчёта бюджета (например, 6): "))
    goals = load_goals()
    results = []
    debt_history = {debt["name"]: {"remaining": debt["amount"], "initial_payment": calculate_annuity_payment(debt["amount"], debt["term"], debt["rate"]), "payment": calculate_annuity_payment(debt["amount"], debt["term"], debt["rate"]), "term": debt["term"], "rate": debt["rate"]} for debt in debts}
    savings_idx = next(i for i, cat in enumerate(categories) if cat["name"] == "Сбережения")
    total_savings = 0

    for month in range(1, num_months + 1):
        current_month = (datetime.now() + timedelta(days=30 * (month - 1))).strftime("%Y-%m")
        fixed_costs = sum(cat["fixed"] or 0 for cat in categories if cat["active"] and cat["fixed"])
        min_costs = sum(cat["min"] for cat in categories if cat["active"] and not cat["fixed"] and cat["name"] != "Сбережения")
        total_debt_payment = sum(debt["payment"] for debt in debt_history.values() if debt["term"] > 0 and debt["remaining"] > 0)
        available_after_fixed = income - fixed_costs - total_debt_payment
        available_for_savings = available_after_fixed - min_costs

        if available_for_savings < 0:
            print(f"Месяц {month}: Недостаточно средств для минимальных расходов.")
            break

        strategy = "max_savings"
        if goals:
            min_savings = min(goal["amount"] / goal["term"] for goal in goals)
            print(f"\nМесяц {month} ({current_month}):")
            print(f"Цель требует {min_savings:.2f} руб./мес., доступно {available_for_savings:.2f} руб./мес.")
            print("Хотите максимум на сбережения или баланс? (макс/запас)")
            choice = input().lower()
            if choice == "макс":
                strategy = "max_savings"
                categories[savings_idx]["min"] = available_for_savings
            else:
                strategy = "balance"
                savings = float(input(f"Введите сумму для сбережений (0–{available_for_savings:.2f}): "))
                savings = max(0, min(available_for_savings, savings))
                categories[savings_idx]["min"] = savings

        result = optimize_budget(income, categories, 0, total_debt_payment, strategy)
        results.append((current_month, result))

        print(f"\nМесяц {month} ({current_month}):")
        for i, cat in enumerate(categories):
            if cat["active"] and result[i] > 0:
                print(f"{cat['name']}: {result[i]:.2f} руб.")
        print(f"Долги: {total_debt_payment:.2f} руб.")
        print(f"Общая сумма: {sum(result) + total_debt_payment:.2f} руб.")

        total_savings += result[savings_idx]
        for debt_name, debt in debt_history.items():
            if debt["term"] > 0 and debt["remaining"] > 0:
                monthly_rate = debt["rate"] / 12
                interest = debt["remaining"] * monthly_rate
                principal = debt["initial_payment"] - interest
                debt["remaining"] = max(0, debt["remaining"] - principal)
                debt["term"] -= 1
                if debt["remaining"] <= 0:
                    debt["payment"] = 0
                    debt["remaining"] = 0
                elif debt["term"] > 0:
                    debt["payment"] = debt["initial_payment"]
                else:
                    debt["payment"] = calculate_annuity_payment(debt["remaining"], max(1, debt["term"]), debt["rate"])
        save_budget_to_history(current_month, income, result, total_debt_payment)

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
    debt_payments = [sum(debt["payment"] for debt in debt_history.values() if debt["term"] > 0 and debt["remaining"] > 0) or 0 for _ in results]

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
    fill_history = input("Хотите заполнить историю? (да/нет)\n")
    if fill_history.lower() == "да":
        income_history = load_income_history()
    else:
        income_history = {}

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
