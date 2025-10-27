import os, sys
from collections import Counter
from multiprocessing import Pool

def classify(path):
    try:
        with open(path) as f:
            content = "".join(f.read(100).split())
            if content.startswith('[{"step":0,'): return "list_based"
            if content.startswith('{"1":{"screenshot":"'): return "dict_based"
            return "other"
    except Exception:
        return "error"

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python verify_traj_json.py <directory>")

    all_files = [os.path.join(r, 'trajectory.json') 
                 for r, _, f in os.walk(sys.argv[1]) if 'trajectory.json' in f]

    if not all_files:
        sys.exit("No 'trajectory.json' files found.")

    with Pool() as p:
        results = p.map(classify, all_files)

    for kind, count in Counter(results).items():
        print(f"{kind}: {count}")
