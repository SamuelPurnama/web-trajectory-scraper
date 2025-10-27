import json
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

import fire
from tqdm import tqdm

from tasks.arxiv.sampling_utils import generate_arxiv_task

ARXIV_SAMPLING_CONFIG = {
    "find_paper_on_arxiv_by_title_via_search_engine": 200,
    "find_paper_on_arxiv_by_title": 200,
    "find_paper_on_arxiv_by_title_and_open_pdf": 200,
    "find_paper_on_arxiv_by_title_and_open_html": 200,
    "find_authors_of_paper_on_arxiv": 500,
    "find_versions_of_paper_on_arxiv": 500,
    "find_category_codes_of_paper_on_arxiv": 500,
    "show_recent_arxiv_listing": 200,
    "arxiv_qa": 500,
    "arxiv_first_lines_of_abstract": 500,
}


def main(
    filepath: str,
    papers_jsonl_filepath: str,
    num_workers: int = 10,
    timeout: int = 60,
    seed: int = 42,
    indent: int = 2,
):
    with open(papers_jsonl_filepath, "r") as file:
        papers_info = [json.loads(line) for line in file]

    task_types = []
    task_counts = []
    for task_type, task_count in ARXIV_SAMPLING_CONFIG.items():
        task_types.append(task_type)
        task_counts.append(task_count)

    num_tasks = sum(task_counts)
    random.seed(seed)
    random.shuffle(papers_info)

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        task_count = 0
        for i, task_type in enumerate(task_types):
            for _ in range(task_counts[i]):
                futures.append(
                    executor.submit(
                        generate_arxiv_task,
                        task_type=task_type,  # pyright: ignore
                        paper_info=papers_info[task_count % len(papers_info)],
                    )
                )
                task_count += 1

        all_tasks = []
        for future in tqdm(as_completed(futures), total=len(futures)):
            try:
                all_tasks.extend(future.result(timeout=timeout))
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
Edit ARXIV_SAMPLING_CONFIG and then run the following:

python -m tasks.arxiv.sample --filepath /root/weka/oe-training-default/webolmo/tanmayg/webolmo-synthetic/tasks/arxiv_tasks.json --papers_jsonl_filepath /root/weka/oe-training-default/webolmo/tanmayg/webolmo-synthetic/arxiv_papers.jsonl
"""
