import json
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

import fire
from tqdm import tqdm

from tasks.s2.sampling_utils import generate_s2_task

S2_SAMPLING_CONFIG = {
    "basic_s2_search": 100,
    "basic_s2_search_and_filter_by_field": 200,
    "basic_s2_search_and_filter_by_has_pdf": 200,
    "s2_search_paper_by_title": 200,
    "s2_find_authors_of_paper": 400,
    "s2_find_citations_of_paper": 200,
    "s2_find_references_of_paper": 200,
    "s2_show_citations_of_paper": 200,
    "s2_show_references_of_paper": 200,
    "s2_show_related_papers": 200,
    "s2_get_citation_blurb": 400,
    "s2_find_author_page": 200,
    "s2_find_author_stats": 200,
    "s2_show_author_details": 200,
    "s2_authors_most": 800,
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
        # papers.extend(search_results["results"])

    random.seed(seed)
    random.shuffle(papers)

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        futures2task_type = dict()
        total_task_count = 0
        for i, (task_type, task_count) in enumerate(S2_SAMPLING_CONFIG.items()):
            for j in range(task_count):
                paper = papers[total_task_count % len(papers)]
                future = executor.submit(
                    generate_s2_task,
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
Edit S2_SAMPLING_CONFIG and then run the following:

python -m tasks.s2.sample --filepath /root/weka/oe-training-default/webolmo/tanmayg/webolmo-synthetic/tasks/s2_tasks.json --s2_papers_json_filepath /root/weka/oe-training-default/webolmo/tanmayg/webolmo-synthetic/s2_papers.json
"""
