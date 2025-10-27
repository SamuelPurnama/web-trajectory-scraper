import json
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

import fire
from tqdm import tqdm

from tasks.amazon.sampling_utils import *
from tasks.amazon.constants import *

AMAZON_SAMPLING_CONFIG = {
    "find_products_on_amazon_by_keyword": 100,
    # "find_products_on_amazon_by_keyword_within_a_price_range": 2,
    "find_products_on_amazon_by_keyword_with_free_shipping": 200,
    "find_products_on_amazon_by_keyword_sort_by_criteria": 100,
    "go_to_top_product_detail_page": 200,
    "summarize_product_details": 300,
    "summarize_product_reviews": 300,
    "summarize_multiple_product_details": 300,
    "summarize_multiple_product_reviews": 300,
    "add_product_to_cart": 300,
    "add_multiple_products_to_cart": 300,
    "add_products_to_cart_and_check_cart": 400,
    "find_bestseller_in_category_via_left_entry": 100,  
    "find_bestseller_in_category_via_top_entry": 100,
}


def main(
    filepath: str,
    num_workers: int = 10,
    timeout: int = 60,
    seed: int = 42,
    indent: int = 2,
):

    random.seed(seed)

    task_types = []
    task_counts = []
    for task_type, task_count in AMAZON_SAMPLING_CONFIG.items():
        task_types.append(task_type)
        task_counts.append(task_count)

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        task_count = 0
        for i, task_type in enumerate(task_types):
            for _ in range(task_counts[i]):
                keyword = random.choice(AMAZON_KEYWORDS)
                # set to default featured as amazon sort by button doesn't work in browsergym
                criteria = "featured" # random.choice(PRODUCT_SORT_CRITERIA)
                category = random.choice(DEPARTMENT_CATEGORIES)
                futures.append(
                    executor.submit(
                        generate_amazon_task,
                        task_type=task_type,  # pyright: ignore
                        keyword=keyword,
                        sort_criteria=criteria,
                        category=category,
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
    breakpoint()


if __name__ == "__main__":
    fire.Fire(main)

"""
Edit AMZON_SAMPLING_CONFIG and then run the following command to generate tasks:

python -m tasks.amazon.sample"
"""
