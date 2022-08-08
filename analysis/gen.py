import random as rdm
from typing import List

from parso.python.tree import Function


def calc_unveil_flakiness(p, fe, n: int, prob):
    """
    :param p: probability of a test passing.
    :param fe: probability of a test failing or error.
    :param n: number of runs.
    :param prob: probability of detecting a flaky test
    :return:
    """
    if prob >= 1 or prob <= 0:
        raise ValueError("Probability between 0 < x < 1 allowed only.")

    npfe = 1 - p - fe
    np = 1 - p
    nfe = 1 - fe
    lsg = 1 - np ** n - nfe ** n + npfe ** n - prob
    return lsg


def fitness_function(p, fe, n, prob):
    lsg = calc_unveil_flakiness(p, fe, n, prob)

    if lsg == 0:
        return 1000000000
    elif lsg < 0:
        return 0
    else:
        return 1 / lsg


def run_gen(init_pop: int, generations: int, p, fe, prob, fitness: Function, stopping_condition: bool):
    print(type(fitness))
    # Initial population
    solutions: List = []
    best_solutions: List = []
    for s in range(init_pop):
        solutions.append((p, fe, int(rdm.uniform(2, 5000)), prob))

    while not stopping_condition:
        for i in range(generations):
            ranked_solutions: List = []
            for s in solutions:
                fit = fitness(s[0], s[1], s[2], s[3])
                ranked_solutions.append((s, fit))
            ranked_solutions.sort(key=lambda y: y[1])
            ranked_solutions.reverse()

            print(f"===== Generation {i} =====")
            print(f"Best solution so far: {ranked_solutions[0]}")

            best_solutions = ranked_solutions[:int(0.1*init_pop)]

            elements: List = []
            for s in best_solutions:
                elements.append(s[0][2])

            # Keep the best 10%
            for j in range(int(0.1 * init_pop)):
                new_gen: List = [(p, fe, elements[j], prob)]

            # Slightly change the best 80%
            for _ in range(int(0.8 * init_pop)):
                new_n = int(rdm.choice(elements) * rdm.uniform(0.98, 1.02))
                new_gen.append((p, fe, new_n, prob))

            # Create new population for the rest 10%
            for _ in range(int(0.1 * init_pop)):
                new_gen.append((p, fe, int(rdm.uniform(2, init_pop*100)), prob))
            solutions = new_gen

        break

    solution = best_solutions[0][0][2]
    return solution


def main() -> None:
    solution = run_gen(init_pop=1000, generations=1000, p=0.0005, fe=0.95, prob=0.95, fitness=fitness_function, stopping_condition=False)
    print(f"NUMBER OF RUNS === {solution}")


if __name__ == "__main__":
    main()
