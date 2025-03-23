# main.py
from ga import optimize_budget
from data import calculate_annuity_payment
from history import (init_db, add_income, get_income, add_category, remove_category, get_categories,
                     add_expenses, add_or_update_debt, get_debts, update_debt_after_payment,
                     add_goal, get_goals, populate_default_categories, populate_history)
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import sqlite3


def get_user_income():
    income = get_income(datetime.now().strftime("%Y-%m"))
    print(f"Доход за {datetime.now().strftime('%Y-%m')}: {income} руб. Хотите обновить? (да/нет)")
    if input().lower() == "да":
        try:
            income = float(input("Введите новый доход: "))
            add_income(datetime.now().strftime("%Y-%m"), income)
        except ValueError:
            print("Ошибка ввода. Оставлен текущий доход.")
    return income


def edit_categories():
    categories = get_categories()
    while True:
        print("\nТекущие категории:")
        for i, cat in enumerate(categories, 1):
            print(f"{i}. {cat['name']} (fixed: {cat['fixed']}, min: {cat['min']}, weight: {cat['weight']}, active: {cat['active']})")
        print("\n1. Добавить категорию\n2. Удалить категорию\n3. Изменить категорию\n4. Завершить")
        choice = input("Выберите действие: ")
        if choice == "1":
            name = input("Название категории: ")
            fixed = input("Фиксированная сумма (или Enter для None): ")
            fixed = float(fixed) if fixed else None
            min_val = float(input("Минимальная сумма: "))
            weight = float(input("Вес (приоритет): "))
            active = int(input("Активна? (1 - да, 0 - нет): "))
            add_category(name, fixed, min_val, weight, active)
            categories = get_categories()
        elif choice == "2":
            idx = int(input("Номер категории для удаления: ")) - 1
            if 0 <= idx < len(categories):
                remove_category(categories[idx]["name"])
                categories = get_categories()
        elif choice == "3":
            idx = int(input("Номер категории для изменения: ")) - 1
            if 0 <= idx < len(categories):
                name = input(f"Новое название ({categories[idx]['name']}): ") or categories[idx]["name"]
                fixed = input(f"Фиксированная сумма ({categories[idx]['fixed']}): ") or str(categories[idx]["fixed"])
                fixed = float(fixed) if fixed and fixed != "None" else None
                min_val = float(input(f"Минимальная сумма ({categories[idx]['min']}): ") or categories[idx]["min"])
                weight = float(input(f"Вес ({categories[idx]['weight']}): ") or categories[idx]["weight"])
                active = int(input(f"Активна? (1/0, текущая: {categories[idx]['active']}): ") or categories[idx]["active"])
                remove_category(categories[idx]["name"])
                add_category(name, fixed, min_val, weight, active)
                categories = get_categories()
        elif choice == "4":
            break


def get_user_debts():
    debts = []
    print("Хотите ввести свои долги? (да/нет)")
    if input().lower() == "да":
        while True:
            name = input("Введите название долга (или 'стоп' для завершения):\n")
            if name.lower() == "стоп":
                break
            try:
                amount = float(input("Общая сумма долга (руб.): "))
                term = int(input("Срок в месяцах: "))
                rate = float(input("Годовая процентная ставка (например, 0.1 для 10%): "))
                monthly_payment = calculate_annuity_payment(amount, term, rate)
                add_or_update_debt(name, amount, monthly_payment, term, rate)
                debts.append({"name": name, "amount": amount, "monthly_payment": monthly_payment, "term": term, "rate": rate})
            except ValueError:
                print("Ошибка ввода. Долг не добавлен.")
    return get_debts()


def get_user_goals():
    print("Хотите задать финансовую цель? (да/нет)")
    if input().lower() == "да":
        name = input("Название цели (например, 'Отпуск'): ")
        amount = float(input("Сумма цели (руб.): "))
        months = int(input("Срок в месяцах: "))
        add_goal(name, amount, months)


def simulate_period(income, categories, debts):
    print("Введите количество месяцев для расчёта бюджета (например, 6):")
    try:
        num_months = int(input())
        if num_months <= 0:
            print("Ошибка: количество месяцев должно быть положительным. Установлено 12 месяцев.")
            num_months = 12
    except ValueError:
        print("Ошибка: введите целое число. Установлено 12 месяцев.")
        num_months = 12

    results = []
    total_debt_payment = sum(debt["monthly_payment"] for debt in debts) if debts else 0
    goals = get_goals()
    min_savings = max(goal["amount"] / goal["months"] for goal in goals) if goals else 0
    savings_idx = next(i for i, cat in enumerate(categories) if cat["name"] == "Сбережения")
    current_income = income * 0.9
    debt_history = [debts]

    for month in range(1, num_months + 1):
        current_month = (datetime.now() + timedelta(days=30 * (month - 1))).strftime("%Y-%m")
        fixed_costs = sum(cat["fixed"] or 0 for cat in categories if cat["active"] and cat["fixed"])
        min_costs = sum(cat["min"] for cat in categories if cat["active"] and not cat["fixed"] and cat["name"] != "Сбережения")
        available_after_fixed = current_income - fixed_costs - total_debt_payment

        if available_after_fixed < 0:
            print(f"Месяц {month}: Недостаточно средств даже для фиксированных расходов и долгов.")
            break

        available_for_savings = available_after_fixed - min_costs
        if available_for_savings < 0:
            print(f"Месяц {month}: Недостаточно средств для минимальных расходов.")
            break

        # Сбрасываем минимальную сумму сбережений
        categories[savings_idx]["min"] = 0
        strategy = "max_savings"

        if goals:
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
                if savings > available_for_savings or savings < 0:
                    savings = max(0, min(available_for_savings, min_savings))
                    print(f"Установлено: {savings:.2f}")
                categories[savings_idx]["min"] = savings

        result = optimize_budget(current_income - total_debt_payment, categories, min_savings, None, strategy)
        results.append((current_month, result))

        add_expenses(current_month, categories, result)
        update_debt_after_payment()
        debts = get_debts()
        total_debt_payment = sum(debt["monthly_payment"] for debt in debts) if debts else 0
        debt_history.append(debts)

        print(f"\nМесяц {month} ({current_month}):")
        for i, cat in enumerate(categories):
            if cat["active"]:
                print(f"{cat['name']}: {result[i]:.2f} руб.")
        if total_debt_payment > 0 or month <= len(debt_history) - 1:
            print(f"Долги: {total_debt_payment:.1f} руб.")
        print(f"Общая сумма: {sum(result) + total_debt_payment:.2f} руб.")

    if goals:
        total_savings = sum(res[savings_idx] for _, res in results)
        print(f"\nИтоговые сбережения за {num_months} мес.: {total_savings:.2f} руб.")
        for goal in goals:
            months_needed = goal["amount"] / total_savings * num_months if total_savings > 0 else float("inf")
            print(f"Цель '{goal['name']}': {goal['amount']} руб. достигнута через {months_needed:.1f} мес.")

    plot_budget_period(results, categories, debt_history, num_months)


def plot_budget_period(results, categories, debt_history, num_months):
    months = [m for m, _ in results]
    savings = [r[next(i for i, cat in enumerate(categories) if cat["name"] == "Сбережения")] for _, r in results]
    total_debts = [sum(debt["monthly_payment"] for debt in debts) if debts else 0 for debts in debt_history[:-1]]

    plt.figure(figsize=(10, 6))
    plt.plot(months, savings, label="Сбережения", marker="o")
    if total_debts:  # Проверяем, есть ли данные о долгах
        plt.plot(months[:len(total_debts)], total_debts, label="Долги", marker="o")
    plt.xlabel("Месяц")
    plt.ylabel("Сумма (руб.)")
    plt.title(f"Динамика бюджета за {num_months} месяцев")
    plt.legend()
    plt.xticks(rotation=45)
    plt.grid()
    plt.show()

    last_result = results[-1][1]
    total_debt_payment = total_debts[-1] if total_debts else 0
    labels = [cat["name"] for cat in categories if cat["active"]] + (["Долги"] if total_debt_payment > 0 else [])
    sizes = [last_result[i] for i, cat in enumerate(categories) if cat["active"]] + ([total_debt_payment] if total_debt_payment > 0 else [])
    plt.figure(figsize=(8, 8))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%')
    plt.title(f"Распределение бюджета в последнем месяце ({num_months}-й месяц)")
    plt.show()


if __name__ == "__main__":
    init_db()
    populate_default_categories()

    fill_history = input("Хотите заполнить историю? (да/нет)\n").lower() == "да"
    if fill_history:
        months = int(input("Сколько месяцев назад заполнить? "))
        populate_history(months)

    income = get_user_income()
    edit_categories()
    categories = get_categories()
    print("\nЗагруженные категории перед оптимизацией:")
    for cat in categories:
        print(cat)

    debts = get_user_debts()
    get_user_goals()
    simulate_period(income, categories, debts)