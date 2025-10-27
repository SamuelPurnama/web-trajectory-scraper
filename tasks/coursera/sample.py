import json
import math
import random
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from concurrent.futures import TimeoutError as FutureTimeoutError

import fire
from sqlalchemy.pool import impl
from tqdm import tqdm

from tasks.persona_utils import read_personas
from tasks.coursera.sampling_utils import (
    COURSERA_TASK_TYPES,
    generate_coursera_task,
)


def main(
    filepath: str,
    personas_filepath: str,
    task_types: list[str] = ['coursera_explore_roles', 'coursera_explore_categories', 'coursera_filter_degrees', 'coursera_search'],
    task_counts: list[int] = [1, 1, 1, 1000],
    keywords_per_persona: list[int] = None,
    tasks_per_keyword: list[int] = None,
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
            )
        )
        task_counts[i] = (
            persona_counts[i] 
        )
    personas = read_personas(personas_filepath)
    random.seed(seed)
    random.shuffle(personas)
    total_tasks = sum(task_counts)

    persona_counter = 0
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        for i, task_type in enumerate(task_types):
            assert (
                task_type in COURSERA_TASK_TYPES
            ), f"task_type should be one of {COURSERA_TASK_TYPES} but got {task_type}"
            for j in range(persona_counts[i]):
                futures.append(
                    executor.submit(
                        generate_coursera_task,
                        persona=personas[persona_counter % len(personas)],
                        task_type=task_type,  # pyright: ignore
                    )
                )
                persona_counter += 1

        all_tasks = []
        for future in tqdm(as_completed(futures), total=len(futures)):
            try:
                all_tasks.extend(future.result(timeout=timeout)["tasks"])
            except FutureTimeoutError:
                print("⏱️ Timed out waiting for a task. Skipping...")
            except Exception as e:
                print(f"❌ Exception in task: {e}")
            finally:
                if not future.done():
                    future.cancel()

    print("all tasks:", all_tasks)
    with open(filepath, "w") as f:
        json.dump(all_tasks, f, indent=indent)


if __name__ == "__main__":
    fire.Fire(main)

"""
python -m tasks.coursera.sample 
--filepath /weka/oe-training-default/piperw/projects/webolmo-synthetic/generated_tasks/coursera_tasks.json 
--personas_filepath /root/weka/prior-default/tanmayg/webolmo-synthetic/100k_personas.jsonl 
"""