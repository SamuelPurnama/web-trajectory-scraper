import json
import math
import random
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

import fire
from tqdm import tqdm

from tasks.persona_utils import read_personas
from tasks.allrecipes_new.sampling_utils import (
    ALL_RECIPES_TASK_TYPES,
    generate_all_recipes_task,
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
    summarize_n: int = 0,
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
                task_type in ALL_RECIPES_TASK_TYPES
            ), f"task_type should be one of {ALL_RECIPES_TASK_TYPES} but got {task_type}"
            for j in range(persona_counts[i]):
                futures.append(
                    executor.submit(
                        generate_all_recipes_task,
                        persona=personas[persona_counter % len(personas)],
                        task_type=task_type,  # pyright: ignore
                        num_keywords=words_per_persona[i],
                        summarize_n=summarize_n,
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
python -m tasks.all_recipes_tasks.sample --filepath  /Users/henna523/Documents/GitHub/browser_agent_tasks/all_recipes_tasks.json  --personas_filepath /Users/henna523/Documents/GitHub/browser_agent_tasks/100k_personas.jsonl --task_types "['all_recipes_basic_search','all_recipes_goto_section','all_recipes_check_reviews','all_recipes_search_directions','all_recipes_search_nutrition_facts','all_recipes_sort_reviews','all_recipes_compare_two_recipes','all_recipes_top_n_recipes','all_recipes_sample_n_recipes','all_recipes_basic_ingredient_search']" --task_counts "[10,10,10,10,10,10,10,10,10,10]" --words_per_persona "[1,1,1,1,1,1,1,1,1,1]" --tasks_per_word "[1,1,1,1,1,1,1,1,1,1]" --summarize_n 3
"""