import json
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

import fire
from tqdm import tqdm

from tasks.espn.sampling_utils import (
    ESPN_TASK_TYPES,
    generate_espn_task,
)

def main(
    filepath: str,
    task_types: list[str],
    task_counts: list[int],
    num_workers: int = 10,
    timeout: int = 60,
    seed: int = 42,
    indent: int = 2,
):
    random.seed(seed)
    
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        for i, task_type in enumerate(task_types):
            assert (
                task_type in ESPN_TASK_TYPES
            ), f"task_type should be one of {ESPN_TASK_TYPES} but got {task_type}"
            for j in range(task_counts[i]):
                futures.append(
                    executor.submit(
                        generate_espn_task,
                        persona="",  # Not used for current task types
                        task_type=task_type,
                        num_words=1,
                        tasks_per_word=1,
                    )
                )

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

uv run -m tasks.espn.sample --filepath espn_tasks.json \
 --task_types "['team_news_nav', 'team_search', 'section_top_headlines', 'create_nfl_team_page_deep_nav', 'create_nba_team_page_deep_nav', 'create_nhl_team_page_deep_nav', 'create_mlb_team_page_deep_nav', 'create_wnba_team_page_deep_nav', 'create_soccer_team_page_deep_nav']" \
 --task_counts "[5, 5, 5, 5, 5, 5, 5, 5, 5]"
"""
