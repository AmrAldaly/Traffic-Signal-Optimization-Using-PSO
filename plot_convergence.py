"""
plot_convergence.py – Visualise PSO convergence from results/pso_results_*.json
================================================================================
Run after pso.py has finished:
    python plot_convergence.py                          # loads the latest run
    python plot_convergence.py results/pso_results_X.json  # loads a specific run
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
    # Auto-select the most recent file in results/ by filename
    # (filenames embed the timestamp as YYYYMMDD_HHMMSS, so lexicographic
    #  order == chronological order — no stat() call needed)
    if not RESULTS_DIR.exists():
        sys.exit("results/ directory not found. Run pso.py first.")

    candidates = sorted(RESULTS_DIR.glob("pso_results_*.json"))
    if not candidates:
        sys.exit("No pso_results_*.json files found in results/. Run pso.py first.")

    json_path = candidates[-1]   # last in sorted order = most recent
    print(f"  Loading latest run → {json_path}")

# ── Load saved results ────────────────────────────────────────────────────
try:
    with open(json_path) as f:
        data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError) as e:
    sys.exit(f"Failed to load {json_path}: {e}")

# ── Extract the run timestamp to link the output image filename ───────────
#    The JSON 'timestamp' field is an ISO string; derive YYYYMMDD_HHMMSS
#    from the source filename itself so the pairing is always exact.
ts_tag = json_path.stem.replace("pso_results_", "")   # e.g. "20240618_143022"

history  = data["history"]
best_pos = data["best_position"]
best_cost = data["best_cost"]
params   = data["params"]

# ── Plot ──────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 5))

ax.plot(range(1, len(history) + 1), history,
        marker='o', linewidth=2, color='#e74c3c', label='Global Best Fitness')
ax.fill_between(range(1, len(history) + 1), history,
                alpha=0.15, color='#e74c3c')

ax.set_title("PSO Convergence – Traffic Signal Optimisation", fontsize=14, fontweight='bold')
ax.set_xlabel("Iteration")
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
plot_path = RESULTS_DIR / f"pso_convergence_{ts_tag}.png"
plt.savefig(plot_path, dpi=150)
print(f"  Plot saved → {plot_path}")
plt.show()
