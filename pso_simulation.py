import json
from traffic_simulation import evaluate


with open("results\\pso_results.json") as f:
    data = json.load(f)
    best_timings = data["best_position"]

print(f"Showing the best result found by PSO: {best_timings}")


evaluate(best_timings, sim_duration=60, headless=False)