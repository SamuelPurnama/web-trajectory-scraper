import ast
import fire
import json
import math
import random
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

from tasks.persona_utils import read_personas
from tasks.huggingface_tasks.sampling_utils import (
    generate_huggingface_task,
    HUGGINGFACE_TASK_TYPES
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
    if isinstance(task_types, str):
        task_types = ast.literal_eval(task_types)
    if isinstance(task_counts, str):
        task_counts = ast.literal_eval(task_counts)

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
    personas = read_personas(personas_filepath)
    random.seed(seed)
    random.shuffle(personas)
    total_tasks = sum(task_counts)

    persona_counter = 0
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        for i, task_type in enumerate(task_types):
            assert (
                task_type in HUGGINGFACE_TASK_TYPES
            ), f"task_type should be one of {HUGGINGFACE_TASK_TYPES} but got {task_type}"
            for j in range(persona_counts[i]):
                futures.append(
                    executor.submit(
                        generate_huggingface_task,
                        persona=personas[persona_counter % len(personas)],
                        task_type=task_type  # pyright: ignore
                    )
                )
                persona_counter += 1

        all_tasks = []
        for future in tqdm(as_completed(futures), total=len(futures)):
            try:
                all_tasks.extend(future.result(timeout=timeout)["tasks"])
            except Exception as e:
                print(
                    f"⚠️ Exception in task {i} (type={task_type}):\n{str(e)}"
                )
            finally:
                if not future.done():
                    future.cancel()

    with open(filepath, "w") as f:
        json.dump(all_tasks, f, indent=indent)


if __name__ == "__main__":
    fire.Fire(main)

"""
uv run tasks/huggingface_tasks/sample.py \
  --filepath /weka/oe-training-default/piperw/projects/webolmo-synthetic/generated_tasks/huggingface/tasks.json \
  --personas_filepath /weka/oe-training-default/webolmo/datasets/100k_personas.jsonl \
  --task_types ['huggingface_search','huggingface_community','huggingface_docs','huggingface_model_lookup_code','huggingface_dataset_lookup_code','huggingface_dataset_filter','huggingface_dataset_open_studio','huggingface_dataset_qa','huggingface_model_qa','huggingface_model_compare_downloads','huggingface_model_filter'] \
  --task_counts [1,1,1,1,1,1,1,1,1,1,1] \
  --num_workers 16
"""

