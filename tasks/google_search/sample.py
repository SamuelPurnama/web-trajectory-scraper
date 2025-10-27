import json
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

import fire
from tqdm import tqdm

from tasks.google_search.sampling_utils import generate_google_search_task

# GSEARCH_SAMPLING_CONFIG = {
#     "google_basic_search": 500,
#     "google_title_search": 500,
#     "google_comparison": 200,
#     "google_subpage_search": 2000,
#     "google_date_filter_search": 500,
#     "google_site_search": 500,
#     "google_qa": 1000,
# }

GSEARCH_SAMPLING_CONFIG = {
    "google_basic_search": 1,
    "google_title_search": 1,
    "google_comparison": 20,
    "google_subpage_search": 1,
    "google_date_filter_search": 1,
    "google_site_search": 1,
    "google_qa": 1,
}


def main(
    filepath: str,
    persona_path: str,
    num_workers: int = 10,
    timeout: int = 60,
    seed: int = 42,
    indent: int = 2,
):

    with open(persona_path, "r") as file:
        personas_jsonl = list(file)

    personas = [json.loads(p)["persona"] for p in personas_jsonl]

    random.seed(seed)
    random.shuffle(personas)

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        futures2task_type = dict()
        total_task_count = 0
        personas
        for i, (task_type, task_count) in enumerate(
            GSEARCH_SAMPLING_CONFIG.items()
        ):
            for j in range(task_count):
                future = executor.submit(
                    generate_google_search_task,
                    persona=personas[(i + j) % len(personas)],
                    task_type=task_type,  # pyright: ignore
                )
                futures.append(future)
                futures2task_type[future] = task_type
                total_task_count += 1

        all_tasks = []
        for future in tqdm(as_completed(futures), total=len(futures)):
            task_type = futures2task_type[future]
            try:
                all_tasks.append(future.result(timeout=timeout))
            except Exception as e:
                print(
                    f"Error in {task_type}n\nError:\n{str(e)}"
                )
            finally:
                if not future.done():
                    future.cancel()

    with open(filepath, "w") as f:
        json.dump(all_tasks, f, indent=indent)


if __name__ == "__main__":
    fire.Fire(main)

"""
Edit GSEARCH_SAMPLING_CONFIG and then run the following:

python -m tasks.google_scholar.sample \
    --filepath gsearch_tasks.json \
    --persona_path persona.jsonl \
"""
