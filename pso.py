"""
pso.py – Particle Swarm Optimization for Traffic Signal Timing
==============================================================
Optimizes [G1, G2, G3, G4] green-phase durations (seconds) to minimize
the fitness score returned by simulation.evaluate().

Usage
-----
    python pso.py                  # runs optimization, prints results
    from pso import run_optimization
    best_pos, best_cost, history = run_optimization()
"""

import random
import copy
import json
from datetime import datetime

from traffic_simulation import evaluate   # fitness function from simulation.py


# =========================================================
# PSO HYPER-PARAMETERS  (tune here)
# =========================================================
SWARM_SIZE   = 15       # number of particles  (10–20 recommended)
ITERATIONS   = 25       # optimisation rounds  (20–30 recommended)
W            = 0.5      # inertia weight        – balances exploration/exploitation
C1           = 1.5      # cognitive coefficient – pull toward personal best
C2           = 1.5      # social coefficient    – pull toward global best

# Search-space bounds for each green time (seconds)
G_MIN = 10
G_MAX = 60

# Velocity clamp: prevents particles flying past the search space in one step
V_MAX = (G_MAX - G_MIN) * 0.5   # 25 s – sensible default

# Simulation settings forwarded to evaluate()
SIM_DURATION = 60       # seconds of simulation per fitness call
HEADLESS     = True     # True = no pygame window during optimisation (faster)

N_SIGNALS = 4           # number of traffic-signal directions (do not change)


# =========================================================
# HELPER UTILITIES
# =========================================================
def _clamp(value, lo, hi):
    return max(lo, min(hi, value))

def _random_position():
    """Uniform random integer position inside [G_MIN, G_MAX]^4."""
    return [random.randint(G_MIN, G_MAX) for _ in range(N_SIGNALS)]

def _random_velocity():
    """Small initial velocity so particles don't shoot past bounds immediately."""
    half = (G_MAX - G_MIN) / 4
    return [random.uniform(-half, half) for _ in range(N_SIGNALS)]

def _round_position(pos):
    """
    Clamp and round each gene to the nearest integer inside [G_MIN, G_MAX].
    Green times must be whole seconds, but velocity arithmetic is done in floats.
    """
    return [int(_clamp(round(p), G_MIN, G_MAX)) for p in pos]


# =========================================================
# PARTICLE
# =========================================================
class Particle:
    """
    A single candidate solution in the swarm.

    Attributes
    ----------
    position   : list[int]   – current [G1, G2, G3, G4]
    velocity   : list[float] – per-dimension velocity
    best_pos   : list[int]   – personal best position seen so far
    best_cost  : float       – fitness at best_pos
    cost       : float       – fitness at current position
    """

    def __init__(self):
        self.position  = _random_position()
        self.velocity  = _random_velocity()
        self.best_pos  = copy.copy(self.position)
        self.cost      = float('inf')
        self.best_cost = float('inf')

    def evaluate(self):
        """Call the simulation and store the result."""
        self.cost = evaluate(self.position, sim_duration=SIM_DURATION, headless=HEADLESS)
        if self.cost < self.best_cost:
            self.best_cost = self.cost
            self.best_pos  = copy.copy(self.position)

    def update_velocity(self, global_best_pos):
        """
        Standard PSO velocity update:
            v = w*v + c1*r1*(pbest - x) + c2*r2*(gbest - x)
        """
        for d in range(N_SIGNALS):
            r1 = random.random()
            r2 = random.random()

            cognitive = C1 * r1 * (self.best_pos[d] - self.position[d])
            social    = C2 * r2 * (global_best_pos[d] - self.position[d])

            self.velocity[d] = W * self.velocity[d] + cognitive + social
            self.velocity[d] = _clamp(self.velocity[d], -V_MAX, V_MAX)

    def update_position(self):
        """Apply velocity, round to integer, enforce bounds."""
        raw = [self.position[d] + self.velocity[d] for d in range(N_SIGNALS)]
        self.position = _round_position(raw)


# =========================================================
# PSO MAIN LOOP
# =========================================================
def run_optimization(
    swarm_size = SWARM_SIZE,
    iterations = ITERATIONS,
    w          = W,
    c1         = C1,
    c2         = C2,
    sim_duration = SIM_DURATION,
    headless   = HEADLESS,
    verbose    = True,
):
    """
    Run PSO to minimise the traffic simulation fitness score.

    Parameters
    ----------
    swarm_size   : int   – number of particles
    iterations   : int   – number of optimisation rounds
    w, c1, c2    : float – PSO constants
    sim_duration : int   – seconds each simulation trial runs for
    headless     : bool  – suppress pygame window during evaluation
    verbose      : bool  – print per-iteration progress

    Returns
    -------
    global_best_pos  : list[int]   – optimised [G1, G2, G3, G4]
    global_best_cost : float       – lowest fitness achieved
    history          : list[float] – best fitness value recorded each iteration
                                     (use this to plot a convergence curve)
    """

    # ── Override module-level defaults so _evaluate() calls respect args ──
    global SIM_DURATION, HEADLESS, W, C1, C2
    SIM_DURATION = sim_duration
    HEADLESS     = headless
    W, C1, C2    = w, c1, c2

    # ── Initialise swarm ──────────────────────────────────────────────
    swarm = [Particle() for _ in range(swarm_size)]

    global_best_pos  = None
    global_best_cost = float('inf')
    history          = []          # best-fitness-per-iteration for convergence plot

    _banner(f"PSO START  |  {swarm_size} particles × {iterations} iterations")

    # ── Evaluate initial positions ────────────────────────────────────
    if verbose:
        print(f"\n{'─'*55}")
        print(f"  Initialising swarm ({swarm_size} particles) …")
        print(f"{'─'*55}")

    for idx, p in enumerate(swarm):
        p.evaluate()
        if verbose:
            print(f"  Particle {idx+1:>2}  pos={p.position}  cost={p.cost:.4f}")
        if p.cost < global_best_cost:
            global_best_cost = p.cost
            global_best_pos  = copy.copy(p.position)

    if verbose:
        print(f"\n  Initial global best → {global_best_pos}  cost={global_best_cost:.4f}")

    # ── Main PSO loop ─────────────────────────────────────────────────
    for it in range(1, iterations + 1):
        _banner(f"Iteration {it}/{iterations}", width=55)

        for idx, p in enumerate(swarm):
            p.update_velocity(global_best_pos)
            p.update_position()
            p.evaluate()

            if p.cost < global_best_cost:
                global_best_cost = p.cost
                global_best_pos  = copy.copy(p.position)

            if verbose:
                marker = " ← NEW BEST" if (p.cost == global_best_cost) else ""
                print(f"  [{it:>2}] P{idx+1:>2}  pos={p.position}  "
                      f"cost={p.cost:.4f}  pbest={p.best_cost:.4f}{marker}")

        history.append(global_best_cost)

        print(f"\n  ★ Iteration {it} best → {global_best_pos}  "
              f"fitness = {global_best_cost:.4f}\n")

    # ── Final report ──────────────────────────────────────────────────
    _print_results(global_best_pos, global_best_cost, history)

    # ── Save convergence data so you can plot it later ────────────────
    _save_history(history, global_best_pos, global_best_cost)

    return global_best_pos, global_best_cost, history


# =========================================================
# OUTPUT HELPERS
# =========================================================
def _banner(text, width=60):
    print(f"\n{'='*width}")
    print(f"  {text}")
    print(f"{'='*width}")

def _print_results(best_pos, best_cost, history):
    _banner("PSO OPTIMISATION COMPLETE")
    print(f"\n  Global Best Position (green times) : {best_pos}")
    print(f"    G1 (→ right) = {best_pos[0]}s")
    print(f"    G2 (↓ down)  = {best_pos[1]}s")
    print(f"    G3 (← left)  = {best_pos[2]}s")
    print(f"    G4 (↑ up)    = {best_pos[3]}s")
    print(f"\n  Global Best Fitness (cost)         : {best_cost:.4f}")
    print(f"  Total iterations                   : {len(history)}")
    print(f"  Improvement (iter 1 → last)        : "
          f"{history[0]:.4f} → {history[-1]:.4f}  "
          f"({_pct_improvement(history[0], history[-1]):.1f}% reduction)")
    print(f"\n  Convergence history (per iteration):")
    for i, h in enumerate(history, start=1):
        bar = '█' * int(h / max(history) * 30) if max(history) > 0 else ''
        print(f"    Iter {i:>2}: {h:>8.4f}  {bar}")
    print()

def _pct_improvement(start, end):
    if start == 0:
        return 0.0
    return (start - end) / start * 100

def _save_history(history, best_pos, best_cost):
    """
    Persist convergence data to JSON so you can plot without re-running PSO.

    Load it in a plotting script with:
        import json
        data = json.load(open('pso_results.json'))
        plt.plot(data['history'])
    """
    payload = {
        "timestamp":       datetime.now().isoformat(),
        "best_position":   best_pos,
        "best_cost":       best_cost,
        "history":         history,
        "params": {
            "swarm_size":   SWARM_SIZE,
            "iterations":   ITERATIONS,
            "w": W, "c1": C1, "c2": C2,
            "g_min": G_MIN, "g_max": G_MAX,
            "sim_duration": SIM_DURATION,
        }
    }
    path = "pso_results.json"
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"  Convergence data saved → {path}")
    print(f"  Plot it with:  python plot_convergence.py\n")


# =========================================================
# ENTRY POINT
# =========================================================
if __name__ == "__main__":
    best_pos, best_cost, history = run_optimization()
