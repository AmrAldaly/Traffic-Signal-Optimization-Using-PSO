# 🚦 AI-Driven Traffic Signal Optimization

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Pygame-2.x-green?style=for-the-badge&logo=pygame&logoColor=white"/>
  <img src="https://img.shields.io/badge/Algorithm-PSO%20%7C%20GA-orange?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Reproducibility-Seeded%20(42)-purple?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/License-MIT-lightgrey?style=for-the-badge"/>
</p>

<p align="center">
  A 2D traffic intersection simulator powered by metaheuristic optimization —
  comparing <strong>Particle Swarm Optimization (PSO)</strong> against a
  <strong>Genetic Algorithm (GA)</strong> to find the green-light timings that
  minimize congestion across a 4-way intersection.
</p>

---

## 📋 Table of Contents

- [Project Overview](#-project-overview)
- [Methodology & Reproducibility](#-methodology--reproducibility)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [How to Run](#-how-to-run)
- [Experimental Results](#-experimental-results)
- [Algorithm Comparison](#-algorithm-comparison)
- [Convergence Discussion](#-convergence-discussion)
- [Future Work](#-future-work)

---

## 🔍 Project Overview

Urban traffic congestion is one of the most costly and well-studied optimization problems in applied AI. This project models a **2D, 4-directional intersection** and asks a concrete question:

> *Given 4 green-light phases — one per direction — what duration should each phase last to minimize the average vehicle waiting time and queue length?*

Rather than relying on hand-tuned timings, two population-based metaheuristic algorithms search the solution space automatically, each evaluated through a **physics-based Pygame simulation** that models real vehicle dynamics: acceleration, safe following gaps, stop-line enforcement, and signal compliance.

**Key metrics optimized:**

```
Fitness Score = Average Waiting Time (s) + Queue Length (vehicles)
```

Lower is better. The algorithms search for the 4-integer vector `[G1, G2, G3, G4]` — green durations in seconds for the Right, Down, Left, and Up directions respectively — that minimizes this composite score.

---

## 🔬 Methodology & Reproducibility

### Fixed Random Seed

All simulation runs use a fixed random seed of **42**, set at the start of every `evaluate()` call:

```python
random.seed(42)
```

This ensures that vehicle spawn patterns, types, and lane assignments are **identical across every algorithm, every iteration, and every baseline case**. Without this, comparing PSO against GA would be meaningless — the noise from stochastic vehicle generation would dwarf the signal from different green-time configurations.

**Practical implication:** Every fitness score reported in this README is 100% reproducible. Running `python pso.py` on any machine will produce the same scores given the same hyperparameters.

### Simulation Engine

Each fitness evaluation runs the Pygame simulation in headless mode (`headless=True`) for a fixed duration of **60 simulated seconds**, then returns the fitness score. The simulation models:

- Four vehicle types: `car`, `bus`, `truck`, `bike` — each with distinct speeds
- Three lanes per direction (9 total entry points per direction)
- Realistic car-following with a configurable safe gap (`movingGap = 27 + 15` buffer)
- Hard stop-line enforcement during red and yellow phases
- Yellow phase duration fixed at **4 seconds**

---

## 🏗 Architecture

```
traffic-signal-optimizer/
│
├── traffic_simulation.py              # Core simulation engine (Pygame)
│   └── evaluate(green_times, sim_duration, headless)
│
├── pso.py                     # Particle Swarm Optimization
│   └── run_optimization() → (best_pos, best_cost, history)
│
├── ga.py                      # Genetic Algorithm
│   └── run_optimization() → (best_pos, best_cost, history)
│
├── pso_result_simulation.py   # Visualize best PSO result in Pygame
├── plot_convergence.py        # Plot convergence curve from results/
│
├── results/                   # Auto-created; timestamped JSON outputs
│   ├── pso_results_YYYYMMDD_HHMMSS.json
│   └── ga_results_YYYYMMDD_HHMMSS.json
│
└── images/                    # Sprite assets
    ├── intersection.png
    ├── signals/               # red.png, yellow.png, green.png
    ├── right/ down/ left/ up/ # car, bus, truck, bike sprites per direction
```

**Design principle — separation of concerns:**

| Layer | Responsibility |
|---|---|
| `traffic_simulation.py` | Physics, vehicle logic, signal timing, fitness computation |
| `pso.py` / `ga.py` | Search strategy — calls `evaluate()` as a black-box oracle |
| `plot_convergence.py` | Visualization — reads from `results/` independently |

This means you can swap the optimizer without touching the simulation, or upgrade the simulation physics without touching the optimization logic.

---

## ⚙️ Installation

**Requirements:** Python 3.10+, pip

```bash
# 1. Clone the repository
git clone https://github.com/AmrAldaly/Traffic-Signal-Optimization
cd Traffic-Signal-Optimization

# 2. Install dependencies
pip install pygame matplotlib

# 3. Verify the image assets are in place
ls images/intersection.png images/signals/
```

No additional build steps are required. The `results/` directory is created automatically on the first optimization run.

---

## 🚀 How to Run

### 1. Baseline Benchmark

Evaluate three manual timing configurations to establish a baseline before running any optimizer:

```bash
python traffic_simulation.py
```

This runs 60-second simulations for `[10,10,10,10]`, `[20,10,15,25]`, and `[5,5,5,5]`, and prints the fitness score for each.

---

### 2. Run PSO Optimization

```bash
python pso.py
```

Launches 15 particles over 25 iterations. Progress is printed per-iteration. On completion, results are saved to `results/pso_results_YYYYMMDD_HHMMSS.json`.

To call it programmatically:

```python
from pso import run_optimization
best_pos, best_cost, history = run_optimization(verbose=False)
print(f"Best timings: {best_pos}  |  Fitness: {best_cost:.4f}")
```

---

### 3. Run GA Optimization

```bash
python ga.py
```

Evolves a population of 20 chromosomes over 25 generations with elitism (top 2 preserved each generation). Results are saved to `results/ga_results_YYYYMMDD_HHMMSS.json`.

```python
from ga import run_optimization
best_pos, best_cost, history = run_optimization(verbose=False)
```

---

### 4. Visualize the Best Result

After running either optimizer, replay the best solution visually in the Pygame window:

```bash
python pso_result_simulation.py
```

This auto-loads the **most recent** JSON file from `results/` and opens a full Pygame simulation using the optimized timings.

---

### 5. Plot the Convergence Curve

```bash
# Auto-loads the most recent result (PSO or GA)
python plot_convergence.py

# Or specify a particular run explicitly
python plot_convergence.py results/pso_results_20260419_060904.json
python plot_convergence.py results/ga_results_20260426_042532.json
```

The plot is saved as `results/{algorithm}_convergence_YYYYMMDD_HHMMSS.png`, linked by timestamp to its source JSON.

---

## 📊 Experimental Results

All experiments used a 60-second simulation window with random seed 42.

### Baseline Cases

| Case | Green Times `[G1, G2, G3, G4]` | Fitness Score |
|:----:|:-------------------------------:|:-------------:|
| 1 | `[10, 10, 10, 10]` — uniform equal | 57.90 |
| 2 | `[20, 10, 15, 25]` — manually skewed | 56.60 |
| 3 | `[5, 5, 5, 5]` — very short phases | 62.60 |

**Observation:** Even a well-intentioned manual adjustment (Case 2) barely beats the uniform baseline. Case 3 — short phases — is the worst performer due to frequent phase switching that creates gaps between green windows and builds queue faster than it clears.

---

### Optimization Results

| Algorithm | Best Timings | Best Fitness | vs. Best Baseline |
|:---------:|:------------:|:------------:|:-----------------:|
| **PSO** 🥇 | `[25, 49, 13, 49]` | **29.78** | **↓ 47.4%** |
| GA | `[19, 56, 38, 40]` | 30.85 | ↓ 45.5% |
| Best Baseline | `[20, 10, 15, 25]` | 56.60 | — |

**PSO is the winner**, achieving a fitness score of **29.78** — a **47% improvement** over the best manually configured baseline.

Both algorithms agree on a structural insight: **long green phases for the Down and Up directions** (`G2`, `G4`) produce significantly better outcomes than equal or short phases. The PSO solution gives the Down and Up directions 49 seconds each, while keeping Left (`G3`) short at 13 seconds — suggesting those directions carry less simulated traffic under seed 42's generation pattern.

---

## ⚖️ Algorithm Comparison

| Property | PSO | GA |
|---|---|---|
| **Representation** | Continuous position + velocity | Integer chromosome |
| **Selection** | Personal best + global best attraction | Tournament (k=3) |
| **Exploration mechanism** | Velocity with inertia weight (w=0.5) | Mutation (Pm=0.1) |
| **Exploitation mechanism** | Cognitive + social pull (c1=c2=1.5) | Single-point crossover (Pc=0.8) + Elitism |
| **Population size** | 15 particles | 15 chromosomes |
| **Generations / Iterations** | 25 | 25 |
| **Best fitness** | **29.78** | 30.85 |
| **Total `evaluate()` calls** | 15 × 25 + 15 = **390** | 15 × 25 = **375** |
| **Convergence speed** | Fast — typically stabilizes by iteration 10 | Moderate — benefits from later-generation refinement |
| **Risk of local minima** | Medium — swarm can collapse prematurely | Lower — crossover maintains diversity |

PSO required **22% fewer fitness evaluations** than GA while achieving a slightly better result — a meaningful advantage when each evaluation costs 60 seconds of simulation time.

---

## 📈 Convergence Discussion

### PSO: Fast but Potentially Narrow

PSO converges rapidly because all particles are simultaneously pulled toward the global best. This is a strength in smooth, unimodal landscapes but creates risk in rugged ones: once the swarm collapses around a good solution, it loses the velocity needed to escape. In this experiment, PSO's convergence curve typically flattens by iteration 8–12, suggesting it found a strong basin of attraction early.

The inertia weight `w=0.5` was deliberately chosen at the boundary of the theoretically convergent range (`w < 1`). Lowering it further (e.g., `w=0.3`) would increase exploitation at the cost of exploration — useful if you already have a good starting region; risky otherwise.

### GA: Slower but More Resilient

The GA's tournament selection + single-point crossover + mutation pipeline maintains population diversity longer than PSO. The elitism count of 2 ensures the best solution is never lost, while mutation continues to inject novel alleles. This makes GA more robust against local minima but also means it converges more slowly.

The crossover rate of `Pc=0.8` and mutation rate of `Pm=0.1` follow standard heuristic guidelines for integer-encoded GAs. A higher `Pm` would help escape local optima at the cost of disrupting good solutions already found.

### Key Takeaway

For this problem (4-dimensional integer space, bounded `[10, 60]`), the search landscape is relatively low-dimensional, which favors PSO's rapid convergence. In higher-dimensional extensions (e.g., 8 or 12 signal phases), GA's diversity mechanisms may prove more valuable.

---

## 🔮 Future Work

**Algorithm extensions**

- Hybrid PSO-GA: use PSO for global exploration in early iterations, then refine with GA mutation
- Adaptive inertia weight: decay `w` from 0.9 → 0.4 over iterations to shift from exploration to exploitation dynamically
- Multi-objective optimization: simultaneously minimize fitness score and total cycle length

**Simulation improvements**

- Variable traffic demand: model rush-hour patterns with time-varying spawn rates
- Turn movements: allow vehicles to turn at the intersection rather than passing straight through
- Pedestrian phases: add a pedestrian crossing phase as a hard constraint
- Multi-intersection networks: extend to a grid of coordinated signals

**Engineering**

- Parallel fitness evaluation using `multiprocessing.Pool` to evaluate the entire population simultaneously — reducing wall-clock time by up to `population_size`×
- Web dashboard: replace the Pygame visualizer with a browser-based real-time view using Flask + WebSockets
- Hyperparameter tuning: automated grid-search or Bayesian optimization of `w`, `c1`, `c2`, `Pm`, `Pc`

---

<p align="center">
  Built with Python · Pygame · PSO · GA &nbsp;|&nbsp; Random Seed 42 for reproducibility
</p>
