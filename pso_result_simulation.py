import os
import glob
import json
from traffic_simulation import evaluate


# ── Find the most recent PSO results file ────────────────────────────────
results_pattern = os.path.join("results", "pso_results_*.json")
matching_files  = sorted(glob.glob(results_pattern))   # lexicographic == chronological

if not matching_files:
    print("No PSO results found. Please run pso.py first.")
    exit()

latest_file = matching_files[-1]
print(f"Loading results from: {latest_file}")

# ── Load best timings ─────────────────────────────────────────────────────
with open(latest_file) as f:
    data = json.load(f)

best_timings = data["best_position"]
best_cost    = data["best_cost"]
params       = data["params"]

print(f"\n  Run timestamp : {data['timestamp']}")
print(f"  Best timings  : G1={best_timings[0]}s  G2={best_timings[1]}s  "
      f"G3={best_timings[2]}s  G4={best_timings[3]}s")
print(f"  Best fitness  : {best_cost:.4f}")
print(f"  PSO params    : swarm={params['swarm_size']}  "
      f"iters={params['iterations']}  w={params['w']}  "
      f"c1={params['c1']}  c2={params['c2']}")

print(f"\nShowing the best result found by PSO: {best_timings}")
print("Opening Pygame window …\n")

# ── Run the visual simulation with the optimised timings ─────────────────
evaluate(best_timings, sim_duration=60, headless=False)
