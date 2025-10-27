import json

with open("4500_espn_tasks.jsonl", "r") as f:
    data = json.load(f)

seen = set()
unique_tasks = []

for task in data:
    step_str = "\n".join(task["steps"])
    if step_str not in seen:
        seen.add(step_str)
        unique_tasks.append(task)

with open("espn_unique_tasks.json", "w") as f:
    json.dump(unique_tasks, f, indent=2)
