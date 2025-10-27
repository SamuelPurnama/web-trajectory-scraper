import json
import math
import random
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

import fire
from tqdm import tqdm

from tasks.persona_utils import read_personas
from tasks.allrecipes.sampling_utils import (
    ALLRECIPES_TASK_TYPES,
    generate_allrecipes_task,
)


def main(
    filepath: str,
    personas_filepath: str,
    task_types: list[str],
    task_counts: list[int],
    tasks_per_persona: list[int],
    num_workers: int = 10,
    timeout: int = 60,
    seed: int = 42,
    indent: int = 2,
):
    persona_counts = []
    for i in range(len(task_counts)):
        persona_counts.append(
            math.ceil(
                task_counts[i]
                / tasks_per_persona[i]
            )
        )
        task_counts[i] = (
            persona_counts[i] * tasks_per_persona[i]
        )
    print(f"Number of personas needed per task type: {persona_counts}")
    personas = read_personas(personas_filepath)
    random.seed(seed)
    random.shuffle(personas)
    total_tasks = sum(task_counts)

    persona_counter = 0
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        for i, task_type in enumerate(task_types):
            assert (
                task_type in ALLRECIPES_TASK_TYPES
            ), f"task_type should be one of {ALLRECIPES_TASK_TYPES} but got {task_type}"
            for j in range(persona_counts[i]):
                futures.append(
                    executor.submit(
                        generate_allrecipes_task,
                        persona=personas[persona_counter % len(personas)],
                        task_type=task_type,  # pyright: ignore
                        num_tasks=tasks_per_persona[i],
                    )
                )
                persona_counter += 1

        all_tasks = []
        for future in tqdm(as_completed(futures), total=len(futures)):
            try:
                all_tasks.extend(future.result(timeout=timeout)["tasks"])
            except Exception as e:
                print(
                    f"Encountered the following exception in one of the tasks: \n{str(e)}"
                )
            finally:
                if not future.done():
                    future.cancel()

    with open(filepath, "w") as f:
        json.dump(all_tasks, f, indent=indent)


if __name__ == "__main__":
    fire.Fire(main)

"""
Example usage:

uv run -m tasks.allrecipes.sample --filepath /root/weka/oe-training-default/webolmo/peters/webolmo-synthetic/tasks/allrecipes_tasks.json --personas_filepath /root/weka/oe-training-default/webolmo/tanmayg/webolmo-synthetic/100k_personas.jsonl --task_types "['allrecipes_recipe_search','allrecipes_ingredient_search']" --task_counts "[2,2]" --tasks_per_persona "[2,2]"

This will generate:
- 10 recipe search tasks (5 personas × 2 tasks each)
- 10 ingredient search tasks (5 personas × 2 tasks each)
"""