import numpy as np
import skfuzzy as fuzz
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Универсумы для переменных
demand = np.arange(0, 101, 1)  # Уровень спроса 0-100%
delivery_time = np.arange(0, 101, 1)  # Время доставки 0-100 условных единиц
sales_forecast = np.arange(0, 101, 1)  # Прогноз продаж 0-100%

# Функции принадлежности для уровня спроса
demand_low = fuzz.trapmf(demand, [0, 0, 20, 40])
demand_medium = fuzz.trapmf(demand, [30, 45, 55, 70])
demand_high = fuzz.trapmf(demand, [60, 80, 100, 100])

# Функции принадлежности для времени доставки
delivery_fast = fuzz.trapmf(delivery_time, [0, 0, 20, 40])
delivery_moderate = fuzz.trapmf(delivery_time, [30, 45, 55, 70])
delivery_slow = fuzz.trapmf(delivery_time, [60, 80, 100, 100])

# Функции принадлежности для прогноза продаж
sales_low = fuzz.trapmf(sales_forecast, [0, 0, 20, 40])
sales_medium = fuzz.trapmf(sales_forecast, [30, 45, 55, 70])
sales_high = fuzz.trapmf(sales_forecast, [60, 80, 100, 100])


def sales_implication(demand_val: int, delivery_val: int) -> np.ndarray:
    # Вычисление степеней принадлежности для уровня спроса
    mu_demand = {
        "low": fuzz.interp_membership(demand, demand_low, demand_val),
        "medium": fuzz.interp_membership(demand, demand_medium, demand_val),
        "high": fuzz.interp_membership(demand, demand_high, demand_val),
    }

    # Вычисление степеней принадлежности для времени доставки
    mu_delivery = {
        "fast": fuzz.interp_membership(delivery_time, delivery_fast, delivery_val),
        "moderate": fuzz.interp_membership(delivery_time, delivery_moderate, delivery_val),
        "slow": fuzz.interp_membership(delivery_time, delivery_slow, delivery_val),
    }

    sales_activations = []

    # База правил для прогнозирования продаж
    rules = {
        ('low', 'fast'): 'low',
        ('low', 'moderate'): 'low',
        ('low', 'slow'): 'low',

        ('medium', 'fast'): 'high',
        ('medium', 'moderate'): 'medium',
        ('medium', 'slow'): 'low',

        ('high', 'fast'): 'high',
        ('high', 'moderate'): 'high',
        ('high', 'slow'): 'medium',
    }

    # Применение правил
    for (d_lvl, t_lvl), sales_lvl in rules.items():
        mu_rule = np.fmin(mu_demand[d_lvl], mu_delivery[t_lvl])
        if sales_lvl == 'low':
            sales_activations.append(np.fmin(mu_rule, sales_low))
        elif sales_lvl == 'medium':
            sales_activations.append(np.fmin(mu_rule, sales_medium))
        elif sales_lvl == 'high':
            sales_activations.append(np.fmin(mu_rule, sales_high))

    # Агрегация результатов
    aggregated = np.fmax.reduce(sales_activations)

    return aggregated


def main() -> None:
    demand_value = float(input("Введите уровень спроса (0-100): "))
    delivery_value = float(input("Введите время доставки (0-100): "))

    result = sales_implication(demand_value, delivery_value)

    # Визуализация результатов
    plt.figure(figsize=(10, 6))

    # Построение функций принадлежности для прогноза продаж
    plt.plot(sales_forecast, sales_low, 'b', linestyle='--', label='Низкие продажи')
    plt.plot(sales_forecast, sales_medium, 'g', linestyle='--', label='Средние продажи')
    plt.plot(sales_forecast, sales_high, 'r', linestyle='--', label='Высокие продажи')

    # Заливка области результата
    plt.fill_between(sales_forecast, 0, result, color='orange', alpha=0.6, label='Результат импликации')

    plt.title(f'Прогнозирование продаж\n(Спрос: {demand_value}, Доставка: {delivery_value})')
    plt.xlabel('Уровень продаж (%)')
    plt.ylabel('Степень принадлежности')
    plt.legend()
    plt.grid(True)
    plt.savefig("sales_forecast.png")
    print("График сохранен в файл 'sales_forecast.png'")


if __name__ == '__main__':
    main()