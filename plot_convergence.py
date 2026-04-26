"""
plot_convergence.py – Visualise PSO or GA convergence from results/*.json
=========================================================================
Run after pso.py or ga.py has finished:
    python plot_convergence.py                            # loads the latest run (PSO or GA)
    python plot_convergence.py results/pso_results_X.json # loads a specific PSO run
    python plot_convergence.py results/ga_results_X.json  # loads a specific GA run
"""

import json
import sys
from pathlib import Path

try:
    import matplotlib.pyplot as plt
except ImportError:
    sys.exit("Install matplotlib first:  pip install matplotlib")


# ── Locate the JSON file to load ─────────────────────────────────────────
RESULTS_DIR = Path("results")

if len(sys.argv) > 1:
    # A specific file was supplied on the command line
    json_path = Path(sys.argv[1])
    if not json_path.exists():
        sys.exit(f"File not found: {json_path}")
else:
    # Auto-select the most recent file in results/ by filename.
    # Covers both pso_results_* and ga_results_* — filenames embed
    # YYYYMMDD_HHMMSS so lexicographic order == chronological order.
    if not RESULTS_DIR.exists():
        sys.exit("results/ directory not found. Run pso.py or ga.py first.")

    candidates = sorted(
        list(RESULTS_DIR.glob("pso_results_*.json")) +
        list(RESULTS_DIR.glob("ga_results_*.json"))
    )
    if not candidates:
        sys.exit("No results found in results/. Run pso.py or ga.py first.")

    json_path = candidates[-1]   # last in sorted order = most recent
    print(f"  Loading latest run → {json_path}")

# ── Load saved results ────────────────────────────────────────────────────
try:
    with open(json_path) as f:
        data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError) as e:
    sys.exit(f"Failed to load {json_path}: {e}")

# ── Derive algorithm label and timestamp from filename ───────────────────
#    stem examples: "pso_results_20240618_143022"  "ga_results_20240618_150900"
stem      = json_path.stem                                  # e.g. "ga_results_20240618_150900"
algorithm = data.get("algorithm", "PSO" if "pso" in stem else "GA")
ts_tag    = stem.split("_", maxsplit=2)[-1]                 # "20240618_150900"

# Colour and x-axis label vary by algorithm
ALGO_COLOR  = '#e74c3c' if algorithm == "PSO" else '#2980b9'
XLABEL      = "Iteration" if algorithm == "PSO" else "Generation"

history  = data["history"]
best_pos = data["best_position"]
best_cost = data["best_cost"]
params   = data["params"]

# ── Plot ──────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 5))

ax.plot(range(1, len(history) + 1), history,
        marker='o', linewidth=2, color=ALGO_COLOR, label='Global Best Fitness')
ax.fill_between(range(1, len(history) + 1), history,
                alpha=0.15, color=ALGO_COLOR)

ax.set_title(f"{algorithm} Convergence – Traffic Signal Optimisation",
             fontsize=14, fontweight='bold')
ax.set_xlabel(XLABEL)
ax.set_ylabel("Fitness Score (Avg Wait + Queue)")
ax.legend()
ax.grid(True, linestyle='--', alpha=0.5)

# Annotate final best
ax.annotate(f"Best: {best_cost:.4f}\n{best_pos}",
            xy=(len(history), history[-1]),
            xytext=(-80, 20), textcoords='offset points',
            arrowprops=dict(arrowstyle='->', color='black'),
            fontsize=9, color='#2c3e50')

plt.tight_layout()
plot_path = RESULTS_DIR / f"{algorithm.lower()}_convergence_{ts_tag}.png"
plt.savefig(plot_path, dpi=150)
print(f"  Plot saved → {plot_path}")
plt.show()
