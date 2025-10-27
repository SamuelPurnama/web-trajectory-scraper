import json
import random

from datasets import load_dataset
from numpy import outer


def read_personas(jsonl_path):
    with open(jsonl_path, "r") as file:
        data = [json.loads(line) for line in file]

    return data


def sample_and_save_personas(jsonl_path, outpath, num_samples=100000):
    data = read_personas(jsonl_path)
    print("before:", len(data))
    data = random.sample(data, min(num_samples, len(data)))
    print("after:", len(data))
    with open(outpath, "w") as outfile:
        for entry in data:
            json.dump(entry, outfile)
            outfile.write("\n")

    return data
