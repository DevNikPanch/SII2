import numpy as np
import matplotlib.pyplot as plt
import random
from typing import List, Tuple, Callable

# Константы
CROPS = ["Wheat", "Corn", "Barley", "Soybean", "Sunflower", "Beet"]
CROP_COSTS = np.array([30, 45, 25, 50, 40, 35])
FIELD_YIELDS = np.array([
    [1.72, 4.13, 2.95, 3.47, 1.59, 4.88],
    [2.34, 3.21, 1.87, 4.45, 2.76, 3.99],
    [4.67, 1.98, 2.43, 3.88, 4.12, 1.34],
    [3.56, 2.67, 4.21, 1.76, 2.91, 3.44],
    [1.88, 4.55, 3.12, 2.34, 1.99, 4.01],
    [2.77, 3.89, 1.45, 4.67, 2.18, 3.22],
    [4.33, 2.12, 3.76, 1.54, 4.88, 2.65],
    [3.11, 1.67, 4.44, 2.23, 3.55, 1.88],
    [2.56, 4.22, 3.33, 1.99, 2.77, 4.66],
    [1.45, 3.88, 2.12, 4.55, 3.01, 2.34]
])

N_FIELDS = FIELD_YIELDS.shape[0]
N_CROPS = len(CROPS)

ALPHA, BETA = 0.6, 0.4
MUTATION_PROBABILITY = 0.5
CROSSOVER_PROBABILITY = 0.7
POPULATION_SIZE = 20
GENERATIONS = 50

MAX_YIELD = np.sum(np.max(FIELD_YIELDS, axis=1))
MAX_COST = N_FIELDS * np.max(CROP_COSTS)


class Individual:
    def __init__(self, genome: np.ndarray):
        self.genome = genome
        self.fitness, self.total_yield, self.total_cost = self.calculate_fitness()

    def calculate_fitness(self) -> Tuple[float, float, float]:
        total_yield = np.sum(FIELD_YIELDS[np.arange(N_FIELDS), self.genome])
        total_cost = np.sum(CROP_COSTS[self.genome])

        norm_yield = total_yield / MAX_YIELD
        norm_cost = total_cost / MAX_COST

        score = ALPHA * norm_yield - BETA * norm_cost
        return score, total_yield, total_cost


def create_random_individual() -> Individual:
    genome = np.random.randint(0, N_CROPS, size=N_FIELDS)
    return Individual(genome)


def select_parents(population: List[Individual]) -> Tuple[Individual, Individual]:
    candidates = random.sample(population, 5)
    candidates.sort(key=lambda x: x.fitness, reverse=True)
    return candidates[0], candidates[1]


def single_point_crossover(parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
    point = np.random.randint(1, N_FIELDS)
    child1 = np.concatenate([parent1.genome[:point], parent2.genome[point:]])
    child2 = np.concatenate([parent2.genome[:point], parent1.genome[point:]])
    return Individual(child1), Individual(child2)


def two_point_crossover(parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
    p1, p2 = sorted(np.random.randint(1, N_FIELDS, size=2))
    child1 = parent1.genome.copy()
    child2 = parent2.genome.copy()
    child1[p1:p2], child2[p1:p2] = parent2.genome[p1:p2], parent1.genome[p1:p2]
    return Individual(child1), Individual(child2)


def uniform_crossover(parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
    mask = np.random.randint(0, 2, size=N_FIELDS).astype(bool)
    child1 = np.where(mask, parent1.genome, parent2.genome)
    child2 = np.where(mask, parent2.genome, parent1.genome)
    return Individual(child1), Individual(child2)


def random_reset(ind: Individual) -> Individual:
    genome = ind.genome.copy()
    pos = np.random.randint(N_FIELDS)
    genome[pos] = np.random.randint(N_CROPS)
    return Individual(genome)


def swap_mutation(ind: Individual) -> Individual:
    genome = ind.genome.copy()
    i, j = np.random.choice(N_FIELDS, 2, replace=False)
    genome[i], genome[j] = genome[j], genome[i]
    return Individual(genome)


def inversion_mutation(ind: Individual) -> Individual:
    genome = ind.genome.copy()
    i, j = sorted(np.random.choice(N_FIELDS, 2, replace=False))
    genome[i:j + 1] = genome[i:j + 1][::-1]
    return Individual(genome)


def evolve_population(population: List[Individual],
                      crossover: Callable,
                      mutation: Callable) -> List[Individual]:
    new_population = []

    while len(new_population) < len(population):
        parent1, parent2 = select_parents(population)

        # Скрещивание
        if random.random() < CROSSOVER_PROBABILITY:
            child1, child2 = crossover(parent1, parent2)
        else:
            child1, child2 = parent1, parent2

        # Мутация
        if random.random() < MUTATION_PROBABILITY:
            child1 = mutation(child1)
        if random.random() < MUTATION_PROBABILITY:
            child2 = mutation(child2)

        new_population.extend([child1, child2])

    return new_population[:len(population)]


def run_experiment(crossover: Callable, mutation: Callable,
                   label: str, color: str, ax: plt.Axes) -> None:
    population = [create_random_individual() for _ in range(POPULATION_SIZE)]
    best_fitness_over_time = []
    best_individuals = []

    for generation in range(GENERATIONS):
        population = evolve_population(population, crossover, mutation)
        best_individual = max(population, key=lambda ind: ind.fitness)
        best_fitness_over_time.append(best_individual.fitness)
        best_individuals.append(best_individual)

    ax.plot(best_fitness_over_time, label=label, color=color, linewidth=2)

    best = best_individuals[-1]
    crop_assignment = [CROPS[crop] for crop in best.genome]

    print(f"{label}:")
    print(f"  Урожай = {best.total_yield:.2f}, Стоимость = {best.total_cost:.2f}, Фитнес = {best.fitness:.3f}")
    print(f"  Назначение культур: {crop_assignment}")
    print("-" * 70)


def main():
    fig, ax = plt.subplots(figsize=(12, 8))

    experiments = [
        (single_point_crossover, random_reset, "Single-point + Reset", "red"),
        (two_point_crossover, random_reset, "Two-point + Reset", "green"),
        (uniform_crossover, random_reset, "Uniform + Reset", "blue"),
        (single_point_crossover, swap_mutation, "Single-point + Swap", "orange"),
        (two_point_crossover, swap_mutation, "Two-point + Swap", "purple"),
        (uniform_crossover, swap_mutation, "Uniform + Swap", "brown"),
        (single_point_crossover, inversion_mutation, "Single-point + Inversion", "pink"),
        (two_point_crossover, inversion_mutation, "Two-point + Inversion", "cyan"),
        (uniform_crossover, inversion_mutation, "Uniform + Inversion", "gray")
    ]

    for crossover, mutation, label, color in experiments:
        run_experiment(crossover, mutation, label, color, ax)

    ax.set_title("Эволюция функции приспособленности для различных операторов", fontsize=14)
    ax.set_xlabel("Поколение")
    ax.set_ylabel("Приспособленность ")
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()