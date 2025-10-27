import json
import math
import random
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

import fire
from sqlalchemy.pool import impl
from tqdm import tqdm

from tasks.persona_utils import read_personas
from tasks.wikipedia.sampling_utils import (
    WIKIPEDIA_TASK_TYPES,
    generate_wikipedia_task,
)


def main(
    filepath: str,
    personas_filepath: str,
    task_types: list[str],
    task_counts: list[int],
    keywords_per_persona: list[int],
    tasks_per_keyword: list[int],
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
                / (keywords_per_persona[i] * tasks_per_keyword[i])
            )
        )
        task_counts[i] = (
            persona_counts[i] * keywords_per_persona[i] * tasks_per_keyword[i]
        )
    print(persona_counts)
    print(task_counts)
    personas = read_personas(personas_filepath)
    random.seed(seed)
    random.shuffle(personas)
    total_tasks = sum(task_counts)

    persona_counter = 0
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        for i, task_type in enumerate(task_types):
            assert (
                task_type in WIKIPEDIA_TASK_TYPES
            ), f"task_type should be one of {WIKIPEDIA_TASK_TYPES} but got {task_type}"
            for j in range(persona_counts[i]):
                futures.append(
                    executor.submit(
                        generate_wikipedia_task,
                        persona=personas[persona_counter % len(personas)],
                        task_type=task_type,  # pyright: ignore
                        num_keywords=keywords_per_persona[i],
                        tasks_per_keyword=tasks_per_keyword[i],
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
$PYTHON -m tasks.wikipedia.sample --filepath /root/weka/oe-training-default/webolmo/tanmayg/webolmo-synthetic/tasks/wikipedia_tasks.json --personas_filepath /root/weka/oe-training-default/webolmo/tanmayg/webolmo-synthetic/100k_personas.jsonl --task_types "['wikipedia_qa','wikipedia_goto_section','wikipedia_basic_search']" --task_counts "[1800,1000,200]" --keywords_per_persona "[3,3,3]" --tasks_per_keyword "[5,5,1]"
"""
