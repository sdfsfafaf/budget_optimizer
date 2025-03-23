# data.py
def calculate_annuity_payment(total, months, interest_rate):
    monthly_rate = interest_rate / 12
    if monthly_rate == 0:
        return total / months
    payment = total * (monthly_rate * (1 + monthly_rate) ** months) / ((1 + monthly_rate) ** months - 1)
    return round(payment)