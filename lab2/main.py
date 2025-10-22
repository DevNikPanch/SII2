import numpy as np
import matplotlib.pyplot as plt


def triangular_mf(x, a, b, c):
    """
    Треугольная функция принадлежности.
    :param x: Точки, для которых вычисляется функция принадлежности.
    :param a: Левая граница начала возрастания функции.
    :param b: Вершина треугольника, где принадлежность равна 1.
    :param c: Правая граница окончания убывания функции.
    :return: Значение функции принадлежности в точках x.
    """
    return np.maximum(0, np.minimum((x - a) / (b - a), (c - x) / (c - b)))


class FuzzySet:
    """Класс для представления нечеткого множества с треугольной функцией принадлежности"""

    def __init__(self, name, a, b, c, color=None):
        self.name = name
        self.a = a
        self.b = b
        self.c = c
        self.color = color

    def get_membership(self, x):
        """Вычисляет степень принадлежности значения x к нечеткому множеству"""
        return triangular_mf(x, self.a, self.b, self.c)

    def __str__(self):
        return f"{self.name}: a={self.a}, b={self.b}, c={self.c}"


class SalesForecastingSystem:
    """Система прогнозирования продаж с нечеткой логикой"""

    def __init__(self):
        self.demand_sets = {
            'низкий': FuzzySet('Низкий спрос', 0, 25, 50, 'blue'),
            'средний': FuzzySet('Средний спрос', 25, 50, 75, 'green'),
            'высокий': FuzzySet('Высокий спрос', 50, 75, 100, 'red')
        }

        self.delivery_sets = {
            'быстро': FuzzySet('Быстрая доставка', 0, 3, 6, 'blue'),
            'умеренно': FuzzySet('Умеренная доставка', 2, 5, 8, 'green'),
            'медленно': FuzzySet('Медленная доставка', 4, 7, 10, 'red')
        }

        self.last_demand_value = None
        self.last_delivery_value = None
        self.last_memberships = {}

    def calculate_membership(self, demand_value, delivery_value):
        self.last_demand_value = demand_value
        self.last_delivery_value = delivery_value
        self.last_memberships = {}

        print("РЕЗУЛЬТАТЫ РАСЧЕТА:")
        print("-" * 30)

        print(f"Для уровня спроса {demand_value}:")
        demand_memberships = {}
        for set_name, fuzzy_set in self.demand_sets.items():
            membership = fuzzy_set.get_membership(np.array([demand_value]))[0]
            demand_memberships[set_name] = membership
            print(f"  {fuzzy_set.name}: {membership:.3f}")

        print(f"\nДля времени доставки {delivery_value}:")
        delivery_memberships = {}
        for set_name, fuzzy_set in self.delivery_sets.items():
            membership = fuzzy_set.get_membership(np.array([delivery_value]))[0]
            delivery_memberships[set_name] = membership
            print(f"  {fuzzy_set.name}: {membership:.3f}")

        self.last_memberships = {
            'demand': demand_memberships,
            'delivery': delivery_memberships
        }

        return demand_memberships, delivery_memberships

    def plot_demand_sets(self, show_user_value=False):
        x = np.linspace(0, 100, 500)

        plt.figure(figsize=(12, 6))

        for set_name, fuzzy_set in self.demand_sets.items():
            y = fuzzy_set.get_membership(x)
            plt.plot(x, y, label=fuzzy_set.name, color=fuzzy_set.color, linewidth=2)

        if show_user_value and self.last_demand_value is not None:
            user_x = self.last_demand_value
            plt.axvline(x=user_x, color='black', linestyle='--', alpha=0.7, linewidth=1)

            plt.text(user_x, 1.05, f'Спрос: {user_x}',
                     ha='center', va='bottom', fontsize=10,
                     bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))

            for set_name, fuzzy_set in self.demand_sets.items():
                membership = self.last_memberships['demand'][set_name]
                if membership > 0:
                    plt.plot(user_x, membership, 'o',
                             color=fuzzy_set.color, markersize=8, markeredgecolor='black', zorder=5)

                    # Добавляем аннотацию с значением принадлежности
                    offset_x = 3 if fuzzy_set.color == 'blue' else -3 if fuzzy_set.color == 'red' else 0
                    offset_y = 0.03 if fuzzy_set.color == 'blue' else -0.03 if fuzzy_set.color == 'red' else 0

                    plt.annotate(f'{membership:.3f}',
                                 (user_x, membership),
                                 textcoords="offset points",
                                 xytext=(offset_x, 10 + offset_y * 100),
                                 ha='center' if offset_x == 0 else 'left' if offset_x > 0 else 'right',
                                 va='bottom',
                                 fontsize=9,
                                 fontweight='bold',
                                 bbox=dict(boxstyle="round,pad=0.2", facecolor=fuzzy_set.color, alpha=0.3))

        plt.title('Нечеткие множества: Уровень спроса', fontsize=14, fontweight='bold', pad=20)
        plt.xlabel('Уровень спроса (единиц)', fontsize=12, labelpad=10)
        plt.ylabel('Принадлежность', fontsize=12, labelpad=10)

        plt.legend(loc='upper right', frameon=True, fancybox=True, shadow=True)

        plt.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)

        plt.ylim(0, 1.15)
        plt.xlim(0, 100)

        plt.yticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
        plt.xticks(np.arange(0, 101, 10))

        plt.gca().spines['top'].set_visible(False)
        plt.gca().spines['right'].set_visible(False)

        plt.tight_layout()
        plt.show()

    def plot_delivery_sets(self, show_user_value=False):
        x = np.linspace(0, 10, 500)

        plt.figure(figsize=(12, 6))

        for set_name, fuzzy_set in self.delivery_sets.items():
            y = fuzzy_set.get_membership(x)
            plt.plot(x, y, label=fuzzy_set.name, color=fuzzy_set.color, linewidth=2)

        if show_user_value and self.last_delivery_value is not None:
            user_x = self.last_delivery_value
            plt.axvline(x=user_x, color='black', linestyle='--', alpha=0.7, linewidth=1)

            plt.text(user_x, 1.05, f'Доставка: {user_x} дн.',
                     ha='center', va='bottom', fontsize=10,
                     bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))

            for set_name, fuzzy_set in self.delivery_sets.items():
                membership = self.last_memberships['delivery'][set_name]
                if membership > 0:
                    plt.plot(user_x, membership, 'o',
                             color=fuzzy_set.color, markersize=8, markeredgecolor='black', zorder=5)

                    offset_x = 0.3 if fuzzy_set.color == 'blue' else -0.3 if fuzzy_set.color == 'red' else 0
                    offset_y = 0.03 if fuzzy_set.color == 'blue' else -0.03 if fuzzy_set.color == 'red' else 0

                    plt.annotate(f'{membership:.3f}',
                                 (user_x, membership),
                                 textcoords="offset points",
                                 xytext=(offset_x * 20, 10 + offset_y * 100),
                                 ha='center' if offset_x == 0 else 'left' if offset_x > 0 else 'right',
                                 va='bottom',
                                 fontsize=9,
                                 fontweight='bold',
                                 bbox=dict(boxstyle="round,pad=0.2", facecolor=fuzzy_set.color, alpha=0.3))

        plt.title('Нечеткие множества: Время доставки', fontsize=14, fontweight='bold', pad=20)
        plt.xlabel('Время доставки (дни)', fontsize=12, labelpad=10)
        plt.ylabel('Принадлежность', fontsize=12, labelpad=10)

        plt.legend(loc='upper right', frameon=True, fancybox=True, shadow=True)

        plt.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)

        plt.ylim(0, 1.15)
        plt.xlim(0, 10)

        plt.yticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
        plt.xticks(np.arange(0, 11, 1))

        plt.gca().spines['top'].set_visible(False)
        plt.gca().spines['right'].set_visible(False)

        plt.tight_layout()
        plt.show()


def main():
    system = SalesForecastingSystem()

    try:
        demand_value = float(input("Введите уровень спроса (0-100 единиц): "))
        delivery_value = float(input("Введите время доставки (0-10 дней): "))

        if 0 <= demand_value <= 100 and 0 <= delivery_value <= 10:
            system.calculate_membership(demand_value, delivery_value)

            # Автоматически показываем графики с результатами
            print("\nСтроим графики с результатами расчетов...")
            system.plot_demand_sets(show_user_value=True)
            system.plot_delivery_sets(show_user_value=True)
        else:
            print("Ошибка: значения должны быть в диапазонах 0-100 для спроса и 0-10 для доставки!")

    except ValueError:
        print("Ошибка: введите числовые значения!")


if __name__ == "__main__":
    main()