import json
import fire
import math
import random
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

from tasks.persona_utils import read_personas
from tasks.wolfram_alpha.sampling_utils import (
    WOLFRAM_TASK_TYPES,
    generate_wolfram_task,
)


def main(
    filepath: str,
    personas_filepath: str,
    task_types: list[str],
    task_counts: list[int],
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
                task_type in WOLFRAM_TASK_TYPES
            ), f"task_type should be one of {WOLFRAM_TASK_TYPES} but got {task_type}"
            for j in range(persona_counts[i]):
                futures.append(
                    executor.submit(
                        generate_wolfram_task,
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
uv run tasks/wolfram_alpha/sample.py \
  --filepath /weka/oe-training-default/piperw/projects/webolmo-synthetic/generated_tasks/wolfram_alpha/tasks.json \
  --personas_filepath /weka/oe-training-default/webolmo/datasets/100k_personas.jsonl \
  --task_types ['wolfram_search','wolfram_choose_category','wolfram_step_by_step_solution','wolfram_plot_expression','wolfram_compare_quantities','wolfram_problem_generator',] \
  --task_counts [1,1,1,1,1,1,] \
  --num_workers 4
"""
