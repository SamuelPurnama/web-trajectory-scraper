import os
import json
import random
from pathlib import Path

def sample_paths(input_dir: str = "extracted_paths", output_file: str = "test_set_3_max_july_23.json", max_samples: int = 3):
    input_dir = Path(input_dir)
    result = {}
    idx = 0

    for file in input_dir.glob("*.json"):
        with open(file, "r") as f:
            data = json.load(f)
            paths = [p for p in data.get("paths", {}).values() if p.get("length", 0) > 1]
            sample = random.sample(paths, min(len(paths), max_samples))
            for entry in sample:
                result[str(idx)] = entry
                idx += 1

    if not output_file.endswith('.json'):
        output_file += '.json'

    with open(output_file, "w") as f:
        json.dump({"paths": result}, f, indent=2)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", '-i', help='Directory of the json files', required=True)
    parser.add_argument("--output-file", '-o',  help='File to save the test set', required=True)
    parser.add_argument("--max-samples", '-max', help='Max number of samples per website', required=True, type=int)
    args = parser.parse_args()
    sample_paths(args.input_dir, args.output_file, args.max_samples)