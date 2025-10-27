import json
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

import fire
from tqdm import tqdm

from tasks.github.sampling_utils import *

GITHUB_SAMPLING_CONFIG = {
    "find_repos_on_github_by_keyword": 100,
    "find_repos_on_github_by_keyword_and_language": 100,
    "find_top_repo_on_github_by_keyword_and_sort_criteria": 200,
    "find_repo_on_github_by_name": 100,
    "go_to_github_repo_readme": 100,
    "github_repo_first_lines_of_readme": 400,
    "find_star_count_of_repo": 100,
    "find_fork_count_of_repo": 100,
    "find_branch_count_of_repo": 100,
    "find_commit_count_of_repo": 100,
    "find_release_count_of_repo": 100,
    "find_open_issue_count_of_repo": 200,
    "find_open_pr_count_of_repo": 200,
    "find_last_commit_time_of_repo": 200,
    "find_license_info_of_repo": 100,
    "find_last_release_version_of_repo": 100,
    "find_top_k_contributors_of_repo": 400,
    "github_qa": 500,
}


def main(
    filepath: str,
    repos_jsonl_filepath: str,
    num_workers: int = 10,
    timeout: int = 60,
    seed: int = 42,
    indent: int = 2,
):
    with open(repos_jsonl_filepath, "r") as file:
        repos_info = [json.loads(line) for line in file]

    task_types = []
    task_counts = []
    for task_type, task_count in GITHUB_SAMPLING_CONFIG.items():
        task_types.append(task_type)
        task_counts.append(task_count)

    num_tasks = sum(task_counts)
    random.seed(seed)
    random.shuffle(repos_info)
    
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        task_count = 0
        repo_task_count = 0
        for i, task_type in enumerate(task_types):
            for _ in range(task_counts[i]):
                if task_type in [
                        "find_repos_on_github_by_keyword",
                        "find_repos_on_github_by_keyword_and_language",
                        "find_top_repo_on_github_by_keyword_and_sort_criteria",
                    ]:
                    keyword = sample_keyword()
                    sort_criteria = sample_repo_sort_criteria()
                    language = sample_language()
                    futures.append(
                        executor.submit(
                            generate_github_task,
                            task_type=task_type,  # pyright: ignore
                            repo_info=None,
                            keyword=keyword,
                            language=language,
                            sort_criteria=sort_criteria,
                        )
                    )
                else:
                    futures.append(
                        executor.submit(
                            generate_github_task,
                            task_type=task_type,  # pyright: ignore
                            repo_info=repos_info[repo_task_count % len(repos_info)],
                        )
                    )
                    repo_task_count += 1
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
Edit GITHUB_SAMPLING_CONFIG and then run the following:

python -m tasks.github.sample --filepath /weka/oe-training-default/zixianm/WebOlmo/webolmo-synthetic/tasks/github/github_tasks.json --repos_jsonl_filepath /weka/oe-training-default/zixianm/WebOlmo/webolmo-synthetic/tasks/github/gitbub_repos.jsonl
"""
