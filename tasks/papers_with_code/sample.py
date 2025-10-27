import json
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

import fire
from tqdm import tqdm

from tasks.papers_with_code.sampling_utils import *

PWC_SAMPLING_CONFIG = {
    # paper tasks
    "find_paper_on_pwc_by_title": 100,
    "find_paper_on_pwc_by_title_and_open_pdf": 100,
    "find_paper_on_pwc_by_title_and_open_abstract": 100,
    "find_authors_of_paper_on_pwc": 100,
    "find_number_of_code_repositories_of_paper_on_pwc": 100,
    "find_tasks_of_paper_on_pwc": 100,
    "find_methods_of_paper_on_pwc": 100,
    "go_to_code_repository_of_paper_on_pwc": 200,
    "go_to_first_dataset_of_paper_on_pwd": 200,
    "go_to_first_task_of_paper_on_pwc": 200,
    "summarize_results_of_paper_on_pwc": 200,
    "pwc_qa": 400,
    # dataset tasks
    "find_dataset_by_name": 100,
    "find_similar_datasets_of_dataset": 100,
    "find_benchmark_count_of_dataset": 100,
    "find_paper_count_of_dataset": 100,
    "go_to_paper_of_dataset": 200,
    "go_to_most_starred_dataloader_of_dataset": 200,
    "go_to_first_benchmark_of_dataset": 200,
    "summarize_usage_of_dataset": 200,
    "pwc_dataset_qa": 400,
}


def main(
    filepath: str,
    papers_filepath: str,
    datasets_filepath: str,
    num_workers: int = 10,
    timeout: int = 60,
    seed: int = 42,
    indent: int = 2,
):
    papers = json.load(open(papers_filepath, "r"))
    datasets = json.load(open(datasets_filepath, "r"))

    task_types = []
    task_counts = []
    for task_type, task_count in PWC_SAMPLING_CONFIG.items():
        task_types.append(task_type)
        task_counts.append(task_count)

    num_tasks = sum(task_counts)
    random.seed(seed)
    random.shuffle(papers)
    random.shuffle(datasets)
    
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        task_count = 0
        paper_task_count = 0
        dataset_task_count = 0
        for i, task_type in enumerate(task_types):
            for _ in range(task_counts[i]):
                if task_type in [
                       "find_paper_on_pwc_by_title",
                        "find_paper_on_pwc_by_title_and_open_pdf",
                        "find_paper_on_pwc_by_title_and_open_abstract",
                        "find_authors_of_paper_on_pwc",
                        "find_number_of_code_repositories_of_paper_on_pwc",
                        "find_tasks_of_paper_on_pwc",
                        "find_first_n_lines_of_abstract_of_paper_on_pwc",
                        "find_methods_of_paper_on_pwc",
                        "go_to_code_repository_of_paper_on_pwc",
                        "go_to_first_dataset_of_paper_on_pwd",
                        "go_to_first_task_of_paper_on_pwc",
                        "summarize_results_of_paper_on_pwc",
                        "pwc_qa",
                    ]:
                    futures.append(
                        executor.submit(
                            generate_pwc_task,
                            task_type=task_type,  # pyright: ignore
                            paper_info=papers[paper_task_count % len(papers)],
                            dataset_info=None,
                        )
                    )
                    paper_task_count += 1
                else:
                    futures.append(
                        executor.submit(
                            generate_pwc_task,
                            task_type=task_type,  # pyright: ignore
                            paper_info=None,
                            dataset_info=datasets[dataset_task_count % len(datasets)],
                        )
                    )
                    dataset_task_count += 1
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
Download papers and datasets from: https://github.com/paperswithcode/paperswithcode-data?tab=readme-ov-file
- papers-with-abstracts.json
- datasets.json

Edit PWC_SAMPLING_CONFIG and then run the following:

python -m tasks.papers_with_code.sample --filepath /weka/oe-training-default/zixianm/WebOlmo/webolmo-synthetic/tasks/papers_with_code/pwc_tasks.json --papers_filepath /weka/oe-training-default/zixianm/WebOlmo/webolmo-synthetic/tasks/papers_with_code/papers-with-abstracts.json --datasets_filepath /weka/oe-training-default/zixianm/WebOlmo/webolmo-synthetic/tasks/papers_with_code/datasets.json
"""
