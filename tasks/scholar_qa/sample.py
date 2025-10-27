import json
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import cast

import fire
from tqdm import tqdm

from tasks.scholar_qa.sampling_utils import (
    SCHOLAR_QA_TASK_TYPES,
    generate_scholar_qa_task,
)

SCHOLAR_QA_SAMPLING_CONFIG = {
    "basic_scholar_qa_search": 600,
    "scholar_qa_search_with_stats": 600,
    "scholar_qa_search_with_titles": 600,
    "scholar_qa_cited_papers": 600,
    "scholar_qa_search_most_relevant": 600,
}


def main(
    filepath: str,
    scholar_qa_queries_filepath: str,
    num_workers: int = 10,
    timeout: int = 60,
    seed: int = 42,
    indent: int = 2,
):
    with open(scholar_qa_queries_filepath, "r") as f:
        scholar_qa_queries = json.load(f)

    random.seed(seed)
    random.shuffle(scholar_qa_queries)

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        futures2taskinfo = dict()
        total_task_count = 0
        for task_type, task_count in SCHOLAR_QA_SAMPLING_CONFIG.items():
            for i in range(task_count):
                query = scholar_qa_queries[i % len(scholar_qa_queries)]["query"]
                future = executor.submit(
                    generate_scholar_qa_task,
                    task_type=task_type,  # pyright: ignore
                    query=query,
                )
                futures.append(future)
                futures2taskinfo[future] = dict(
                    task_type=task_type,
                    query=query,
                )
                total_task_count += 1

        all_tasks = []
        for future in tqdm(as_completed(futures), total=total_task_count):
            task_info = futures2taskinfo[future]
            try:
                all_tasks.append(future.result(timeout=timeout))
            except TimeoutError:
                print(f"Timeout error for task {task_info}")
            except Exception as e:
                print(f"Error for task {task_info}: {e}")
            finally:
                if not future.done():
                    future.cancel()

    with open(filepath, "w") as f:
        json.dump(all_tasks, f, indent=indent)


if __name__ == "__main__":
    fire.Fire(main)
    """
    Edit SCHOLAR_QA_SAMPLING_CONFIG and then run the following:
    python -m tasks.scholar_qa.sample --filepath /root/weka/oe-training-default/webolmo/tanmayg/webolmo-synthetic/tasks/scholar_qa_tasks.json --scholar_qa_queries_filepath /root/weka/oe-training-default/webolmo/tanmayg/webolmo-synthetic/scholar_qa_selected_queries.json
    """
