#!/usr/bin/env python3

import json
import sys

def filter_duplicate_tasks(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    seen_steps = set()
    filtered_tasks = []
    
    for task in data:
        steps = task.get('steps', [])
        steps_str = json.dumps(steps, sort_keys=True)
        
        if steps_str not in seen_steps:
            seen_steps.add(steps_str)
            filtered_tasks.append(task)
    
    with open(json_file, 'w') as f:
        json.dump(filtered_tasks, f, indent=2)
    
    print(f'Filtered {len(data)} tasks down to {len(filtered_tasks)} unique tasks')

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python deduplicate_tasks.py <json_file>")
        sys.exit(1)
    
    filter_duplicate_tasks(sys.argv[1])
