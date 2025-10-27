import json
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

import fire
from tqdm import tqdm

from tasks.google_scholar.sampling_utils import (
    GSCHOLAR_TASK_TYPES,
    generate_gscholar_task,
)

GSCHOLAR_SAMPLING_CONFIG = {
    "basic_gscholar_search": 100,
    "basic_gscholar_author_search": 100,
    "basic_gscholar_title_search": 100,
    "gscholar_open_paper_page": 100,
    "gscholar_paper_citation_count": 200,
    "gscholar_paper_citation_blurb": 300,
    "gscholar_paper_related_articles": 100,
    "gscholar_author_info": 600,
    "gscholar_author_citation_info": 1000,
    "gscholar_authors_most_cited_papers": 500,
    "gscholar_sort_by_year": 200,
    "gscholar_most_recent_papers": 400,
}


def main(
    filepath: str,
    s2_papers_json_filepath: str,
    num_workers: int = 10,
    timeout: int = 60,
    seed: int = 42,
    indent: int = 2,
):
    with open(s2_papers_json_filepath, "r") as file:
        s2_papers = json.load(file)

    papers = []
    for search_results in s2_papers:
        keyword = search_results["keyword"]
        field = search_results["field"]
        for paper in search_results["results"]:
            paper["keyword"] = keyword
            paper["field"] = field
            if len(paper["authors"]) > 0:
                papers.append(paper)

    random.seed(seed)
    random.shuffle(papers)

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        futures2task_type = dict()
        total_task_count = 0
        for i, (task_type, task_count) in enumerate(
            GSCHOLAR_SAMPLING_CONFIG.items()
        ):
            for j in range(task_count):
                paper = papers[total_task_count % len(papers)]
                future = executor.submit(
                    generate_gscholar_task,
                    task_type=task_type,  # pyright: ignore
                    paper=paper,
                )
                futures.append(future)
                futures2task_type[future] = (task_type, paper)
                total_task_count += 1

        all_tasks = []
        for future in tqdm(as_completed(futures), total=len(futures)):
            task_type, paper = futures2task_type[future]
            try:
                all_tasks.append(future.result(timeout=timeout))
            except Exception as e:
                print(
                    f"Error in {task_type} with paper:\n{paper}\n\nError:\n{str(e)}"
                )
            finally:
                if not future.done():
                    future.cancel()

    with open(filepath, "w") as f:
        json.dump(all_tasks, f, indent=indent)


if __name__ == "__main__":
    fire.Fire(main)

"""
Edit GSCHOLAR_SAMPLING_CONFIG and then run the following:

python -m tasks.google_scholar.sample --filepath /root/weka/oe-training-default/webolmo/tanmayg/webolmo-synthetic/tasks/gscholar_tasks.json --s2_papers_json_filepath /root/weka/oe-training-default/webolmo/tanmayg/webolmo-synthetic/s2_papers.json
"""
