"""
plot_convergence.py – Visualise PSO convergence from saved pso_results.json
============================================================================
Run after pso.py has finished:
    python plot_convergence.py
"""

import json
import sys

try:
    import matplotlib.pyplot as plt
except ImportError:
    sys.exit("Install matplotlib first:  pip install matplotlib")

# ── Load saved results ────────────────────────────────────────────────────
try:
    with open("pso_results.json") as f:
        data = json.load(f)
except FileNotFoundError:
    sys.exit("pso_results.json not found. Run pso.py first.")

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
plt.savefig("pso_convergence.png", dpi=150)
print("Saved → pso_convergence.png")
plt.show()
