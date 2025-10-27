import json
import math
import random
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

import fire
from tqdm import tqdm

from tasks.persona_utils import read_personas
from tasks.cambridge_dictionary_tasks.sampling_utils import (
    CAMBRIDGE_DICTIONARY_TASK_TYPES,
    generate_cambridge_dictionary_task,
)


def main(
    filepath: str,
    personas_filepath: str,
    task_types: list[str],
    task_counts: list[int],
    words_per_persona: list[int],
    tasks_per_word: list[int],
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
                / (words_per_persona[i] * tasks_per_word[i])
            )
        )
        task_counts[i] = (
            persona_counts[i] * words_per_persona[i] * tasks_per_word[i]
        )
    print(persona_counts)
    personas = read_personas(personas_filepath)
    random.seed(seed)
    random.shuffle(personas)
    total_tasks = sum(task_counts) # unused for now. 

    persona_counter = 0
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        for i, task_type in enumerate(task_types):
            assert (
                task_type in CAMBRIDGE_DICTIONARY_TASK_TYPES
            ), f"task_type should be one of {CAMBRIDGE_DICTIONARY_TASK_TYPES} but got {task_type}"
            for j in range(persona_counts[i]):
                futures.append(
                    executor.submit(
                        generate_cambridge_dictionary_task,
                        persona=personas[persona_counter % len(personas)],
                        task_type=task_type,  # pyright: ignore
                        num_words=words_per_persona[i],
                        tasks_per_word=tasks_per_word[i],
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
python -m tasks.cambridge_dictionary_tasks.sample --filepath /Users/peters/Desktop/webolmo_code/webolmo-synthetic/tasks/cambridge_dictionary_tasks.json --personas_filepath /Users/peters/Downloads/100k_personas.jsonl --task_types "['cambridge_dictionary_basic_search','cambridge_dictionary_goto_section']" --task_counts "[5,5]" --words_per_persona "[1,1]" --tasks_per_word "[1,1]"
"""