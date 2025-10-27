import json
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

import fire
from tqdm import tqdm

from tasks.apple.sampling_utils import generate_apple_task, APPLE_TASK_TYPES


APPLE_SAMPLING_CONFIG = {
    "apple_check_price": 400,
    "apple_search_accessories": 400,
    "apple_navigate_page": 400,
    "apple_sort_accessories": 500,
    "apple_support": 300,
    "apple_find_store_locator": 500,
    "apple_qa": 500,
    "apple_support_qa": 500,
    "apple_tech_specs": 400,
    "apple_tech_specs_qa": 500,
}


def main(
    filepath: str,
    num_workers: int = 10,
    timeout: int = 60,
    seed: int = 42,
    indent: int = 2,
):
    random.seed(seed)
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        fut2type = {}
        for task_type, count in APPLE_SAMPLING_CONFIG.items():
            for _ in range(count):
                f = executor.submit(generate_apple_task, task_type)
                futures.append(f)
                fut2type[f] = task_type

        all_tasks = []
        for f in tqdm(as_completed(futures), total=len(futures)):
            tt = fut2type[f]
            try:
                all_tasks.append(f.result(timeout=timeout))
            except Exception as e:
                print(f"Error in {tt}:\n  {e}")
            finally:
                if not f.done():
                    f.cancel()

    with open(filepath, "w") as out:
        json.dump(all_tasks, out, indent=indent)


if __name__ == "__main__":
    fire.Fire(main)

"""
Edit APPLE_SAMPLING_CONFIG and then run the following:

python -m tasks.apple.sample \
    --filepath apple_tasks.json
"""
