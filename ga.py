"""
ga.py – Genetic Algorithm for Traffic Signal Timing
=====================================================
Optimizes [G1, G2, G3, G4] green-phase durations (seconds) to minimize
the fitness score returned by simulation.evaluate().

Mirrors the structure of pso.py so that plot_convergence.py works on GA
results with minimal changes (swap the glob pattern from pso_results_*
to ga_results_* and the file loads identically).

Usage
-----
    python ga.py                   # runs optimization, prints results
    from ga import run_optimization
    best_pos, best_cost, history = run_optimization()
"""

import random
import copy
import json
from datetime import datetime
from pathlib import Path

from traffic_simulation import evaluate   # same fitness function used by pso.py


# =========================================================
# GA HYPER-PARAMETERS  (tune here)
# =========================================================
POP_SIZE        = 15        # number of chromosomes in each generation
ITERATIONS      = 25        # number of generations to evolve
TOURNAMENT_K    = 3         # tournament size for selection (2–5 is typical)
CROSSOVER_RATE  = 0.8       # probability that two parents actually crossover
MUTATION_RATE   = 0.1       # per-gene probability of random mutation

# Search-space bounds — identical to pso.py for a fair comparison
G_MIN = 10
G_MAX = 60

# Simulation settings forwarded to evaluate()
SIM_DURATION = 60           # seconds of simulation per fitness call
HEADLESS     = True         # True = no pygame window during optimisation

N_SIGNALS = 4               # number of traffic-signal directions (do not change)

ELITISM_COUNT = 2           # top-N chromosomes copied unchanged each generation
                            # (set to 0 to disable elitism)


# =========================================================
# HELPER UTILITIES
# =========================================================
def _random_chromosome():
    """Uniform random integer chromosome inside [G_MIN, G_MAX]^4."""
    return [random.randint(G_MIN, G_MAX) for _ in range(N_SIGNALS)]

def _clamp_chromosome(chrom):
    """Ensure every gene stays within [G_MIN, G_MAX] after crossover/mutation."""
    return [max(G_MIN, min(G_MAX, g)) for g in chrom]


# =========================================================
# SELECTION  –  Tournament Selection
# =========================================================
def _tournament_select(population, fitnesses, k=TOURNAMENT_K):
    """
    Pick k individuals at random, return the one with the lowest fitness
    (minimisation problem).

    Tournament selection is preferred over roulette wheel here because
    it works equally well whether fitness values are close together or
    orders-of-magnitude apart, and it does not require fitness scaling.

    Parameters
    ----------
    population : list[list[int]]  – current generation
    fitnesses  : list[float]      – evaluated cost for each chromosome
    k          : int              – tournament size

    Returns
    -------
    list[int]  – a copy of the winning chromosome
    """
    indices  = random.sample(range(len(population)), k)
    winner   = min(indices, key=lambda i: fitnesses[i])
    return copy.copy(population[winner])


# =========================================================
# CROSSOVER  –  Single-Point Crossover
# =========================================================
def _single_point_crossover(parent_a, parent_b):
    """
    With probability CROSSOVER_RATE, cut both parents at a random point
    and swap their tails to produce two children.  If crossover does not
    fire, the parents are returned unchanged (standard GA behaviour).

    Example (N_SIGNALS=4, cut after index 1):
        parent_a = [G1a, G2a | G3a, G4a]
        parent_b = [G1b, G2b | G3b, G4b]
        child_a  = [G1a, G2a,  G3b, G4b]
        child_b  = [G1b, G2b,  G3a, G4a]

    Returns
    -------
    (child_a, child_b) : tuple[list[int], list[int]]
    """
    if random.random() < CROSSOVER_RATE and N_SIGNALS > 1:
        point   = random.randint(1, N_SIGNALS - 1)   # at least 1 gene from each parent
        child_a = parent_a[:point] + parent_b[point:]
        child_b = parent_b[:point] + parent_a[point:]
    else:
        child_a = copy.copy(parent_a)
        child_b = copy.copy(parent_b)

    return child_a, child_b


# =========================================================
# MUTATION  –  Uniform Random Mutation
# =========================================================
def _mutate(chromosome):
    """
    For each gene, with probability MUTATION_RATE replace it with a new
    random integer in [G_MIN, G_MAX].

    Mutation is applied in-place and the mutated chromosome is returned.
    """
    for i in range(N_SIGNALS):
        if random.random() < MUTATION_RATE:
            chromosome[i] = random.randint(G_MIN, G_MAX)
    return chromosome


# =========================================================
# GA MAIN LOOP
# =========================================================
def run_optimization(
    pop_size       = POP_SIZE,
    iterations     = ITERATIONS,
    tournament_k   = TOURNAMENT_K,
    crossover_rate = CROSSOVER_RATE,
    mutation_rate  = MUTATION_RATE,
    elitism_count  = ELITISM_COUNT,
    sim_duration   = SIM_DURATION,
    headless       = HEADLESS,
    verbose        = True,
):
    """
    Run the Genetic Algorithm to minimise the traffic simulation fitness score.

    Parameters
    ----------
    pop_size       : int   – number of chromosomes per generation
    iterations     : int   – number of generations
    tournament_k   : int   – tournament selection size
    crossover_rate : float – probability of crossover firing
    mutation_rate  : float – per-gene mutation probability
    elitism_count  : int   – top-N survivors copied unchanged each generation
    sim_duration   : int   – seconds each simulation trial runs for
    headless       : bool  – suppress pygame window during evaluation
    verbose        : bool  – print per-generation best fitness

    Returns
    -------
    best_pos   : list[int]   – optimised [G1, G2, G3, G4]
    best_cost  : float       – lowest fitness achieved
    history    : list[float] – best fitness per generation (convergence curve)
    """

    # ── Override module-level defaults so helpers pick up runtime args ──
    global SIM_DURATION, HEADLESS, MUTATION_RATE, CROSSOVER_RATE, TOURNAMENT_K
    SIM_DURATION   = sim_duration
    HEADLESS       = headless
    MUTATION_RATE  = mutation_rate
    CROSSOVER_RATE = crossover_rate
    TOURNAMENT_K   = tournament_k

    # ── Initialise population ─────────────────────────────────────────
    population = [_random_chromosome() for _ in range(pop_size)]
    fitnesses  = [float('inf')] * pop_size

    global_best_pos  = None
    global_best_cost = float('inf')
    history          = []

    _banner(f"GA START  |  pop={pop_size}  gens={iterations}  "
            f"Pc={crossover_rate}  Pm={mutation_rate}  k={tournament_k}")

    # ── Evaluate Generation 0 ─────────────────────────────────────────
    if verbose:
        print(f"\n{'─'*55}")
        print(f"  Initialising population ({pop_size} chromosomes) …")
        print(f"{'─'*55}")

    for idx in range(pop_size):
        fitnesses[idx] = evaluate(population[idx],
                                  sim_duration=SIM_DURATION,
                                  headless=HEADLESS)
        if verbose:
            print(f"  Chrom {idx+1:>2}  genes={population[idx]}  "
                  f"cost={fitnesses[idx]:.4f}")
        if fitnesses[idx] < global_best_cost:
            global_best_cost = fitnesses[idx]
            global_best_pos  = copy.copy(population[idx])

    if verbose:
        print(f"\n  Initial global best → {global_best_pos}  "
              f"cost={global_best_cost:.4f}")

    # ── Generational loop ─────────────────────────────────────────────
    for gen in range(1, iterations + 1):
        _banner(f"Generation {gen}/{iterations}", width=55)

        next_population = []
        next_fitnesses  = []

        # ── Elitism: carry top chromosomes forward unchanged ──────────
        if elitism_count > 0:
            elite_indices = sorted(range(pop_size),
                                   key=lambda i: fitnesses[i])[:elitism_count]
            for ei in elite_indices:
                next_population.append(copy.copy(population[ei]))
                next_fitnesses.append(fitnesses[ei])
                if verbose:
                    print(f"  [elite]  genes={population[ei]}  "
                          f"cost={fitnesses[ei]:.4f}")

        # ── Fill the rest of the new population ───────────────────────
        while len(next_population) < pop_size:
            # Selection
            parent_a = _tournament_select(population, fitnesses, tournament_k)
            parent_b = _tournament_select(population, fitnesses, tournament_k)

            # Crossover
            child_a, child_b = _single_point_crossover(parent_a, parent_b)

            # Mutation
            child_a = _mutate(_clamp_chromosome(child_a))
            child_b = _mutate(_clamp_chromosome(child_b))

            # Evaluate children
            for child in (child_a, child_b):
                if len(next_population) >= pop_size:
                    break
                cost = evaluate(child, sim_duration=SIM_DURATION, headless=HEADLESS)
                next_population.append(child)
                next_fitnesses.append(cost)

                if cost < global_best_cost:
                    global_best_cost = cost
                    global_best_pos  = copy.copy(child)

                if verbose:
                    marker = " ← NEW BEST" if cost == global_best_cost else ""
                    print(f"  [{gen:>2}] genes={child}  cost={cost:.4f}{marker}")

        # ── Replace generation ────────────────────────────────────────
        population = next_population
        fitnesses  = next_fitnesses

        history.append(global_best_cost)

        gen_best_idx  = fitnesses.index(min(fitnesses))
        gen_best_cost = fitnesses[gen_best_idx]
        print(f"\n  ★ Generation {gen} best → {population[gen_best_idx]}  "
              f"fitness = {gen_best_cost:.4f}  "
              f"[global best = {global_best_cost:.4f}]\n")

    # ── Final report ──────────────────────────────────────────────────
    _print_results(global_best_pos, global_best_cost, history, iterations)

    # ── Save convergence data ─────────────────────────────────────────
    _save_history(history, global_best_pos, global_best_cost,
                  pop_size, iterations,
                  crossover_rate, mutation_rate, tournament_k, elitism_count)

    return global_best_pos, global_best_cost, history


# =========================================================
# OUTPUT HELPERS  (mirrored from pso.py)
# =========================================================
def _banner(text, width=60):
    print(f"\n{'='*width}")
    print(f"  {text}")
    print(f"{'='*width}")

def _pct_improvement(start, end):
    if start == 0:
        return 0.0
    return (start - end) / start * 100

def _print_results(best_pos, best_cost, history, iterations):
    _banner("GA OPTIMISATION COMPLETE")
    print(f"\n  Global Best Position (green times) : {best_pos}")
    print(f"    G1 (→ right) = {best_pos[0]}s")
    print(f"    G2 (↓ down)  = {best_pos[1]}s")
    print(f"    G3 (← left)  = {best_pos[2]}s")
    print(f"    G4 (↑ up)    = {best_pos[3]}s")
    print(f"\n  Global Best Fitness (cost)         : {best_cost:.4f}")
    print(f"  Total generations                  : {iterations}")
    print(f"  Improvement (gen 1 → last)         : "
          f"{history[0]:.4f} → {history[-1]:.4f}  "
          f"({_pct_improvement(history[0], history[-1]):.1f}% reduction)")
    print(f"\n  Convergence history (per generation):")
    for i, h in enumerate(history, start=1):
        bar = '█' * int(h / max(history) * 30) if max(history) > 0 else ''
        print(f"    Gen  {i:>2}: {h:>8.4f}  {bar}")
    print()

def _save_history(history, best_pos, best_cost,
                  pop_size, iterations,
                  crossover_rate, mutation_rate, tournament_k, elitism_count):
    """
    Save convergence data to results/ga_results_YYYYMMDD_HHMMSS.json.

    The JSON structure is intentionally identical to pso.py's output so
    that plot_convergence.py only needs its glob pattern changed.
    """
    # ── 1. Ensure results/ exists ─────────────────────────────────────
    results_dir = Path("results")
    results_dir.mkdir(parents=True, exist_ok=True)

    # ── 2. Unique filename from timestamp ────────────────────────────
    ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ga_results_{ts}.json"
    path     = results_dir / filename

    # ── 3. Payload (same top-level keys as pso.py) ────────────────────
    payload = {
        "timestamp":     datetime.now().isoformat(),
        "algorithm":     "GA",                    # extra field for comparison scripts
        "best_position": best_pos,
        "best_cost":     best_cost,
        "history":       history,
        "params": {
            "pop_size":       pop_size,
            "iterations":     iterations,
            "crossover_rate": crossover_rate,
            "mutation_rate":  mutation_rate,
            "tournament_k":   tournament_k,
            "elitism_count":  elitism_count,
            "g_min":          G_MIN,
            "g_max":          G_MAX,
            "sim_duration":   SIM_DURATION,
        }
    }

    # ── 4. Exclusive write – never overwrites an existing file ────────
    with open(path, "x") as f:
        json.dump(payload, f, indent=2)

    print(f"  Convergence data saved → {path}")
    print(f"  Plot it with:  python plot_convergence.py\n")


# =========================================================
# ENTRY POINT
# =========================================================
if __name__ == "__main__":
    best_pos, best_cost, history = run_optimization()
