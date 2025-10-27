import json
import math
import random
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

import fire
from sqlalchemy.pool import impl
from tqdm import tqdm

from tasks.persona_utils import read_personas
from tasks.satlas.sampling_utils import (
    SATLAS_TASK_TYPES,
    generate_satlas_task,
)


def main(
    filepath: str,
    personas_filepath: str = None,
    task_types: list[str] = ['satlas_map_qa_task'],
    task_counts: list[int] = [500],
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
                task_type in SATLAS_TASK_TYPES
            ), f"task_type should be one of {SATLAS_TASK_TYPES} but got {task_type}"
            for j in range(persona_counts[i]):
                futures.append(
                    executor.submit(
                        generate_satlas_task,
                        persona=personas[persona_counter % len(personas)],
                        task_type=task_type,  # pyright: ignore
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
uv run tasks/satlas/sample.py \
--filepath generated_tasks/satlas_tasks.json \
--personas_filepath /Users/piperwolters/projects/100k_personas.jsonl \
--task_types "['satlas_map_qa_task']" \
--task_counts "[5]" 
"""
