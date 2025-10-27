import ell
from pydantic import BaseModel, Field
from faker import Faker

import random
import inspect
from typing import Literal

from tasks.instruction_utils import get_instruction
from tasks.apple.constants import PRODUCTS, PAGES, SORT_BY, BASIC_SUPPORT_ITEMS


def create_apple_qa_task(product: str) -> dict:
    class Question(BaseModel):
        question: str = Field(
            description=f"Factual question you'd search on Apple.com about '{product}'"
        )

    @ell.complex(model="gpt-4o", response_format=Question)
    def lmp(product: str):
        return [
            ell.user(
                f"Generate one concise factual question you would answer on Apple.com about '{product}'"
            )
        ]

    question = lmp(product).parsed.question  # type: ignore

    steps = [
        "Go to https://www.apple.com",
        f"Click the search icon and type in '{question}' and press Enter",
        "On the results page, scroll down until you find the result that best answers the question and click on that result",
        "Extract the answer from the page",
        "Exit",
    ]
    return {
        "task_type": "apple_qa",
        "product": product,
        "question": question,
        "steps": steps,
    }


def create_apple_check_price_task(page: str, product: str) -> dict:
    steps = [
        "Go to https://www.apple.com",
        f"Click on '{page}' in the top navigation bar",
        f"Scroll down until you find the '{product}' product",
        f"Click on the '{product}' product to view its details",
        "Scroll down until the price is visible",
        "Exit",
    ]
    return {
        "task_type": "apple_check_price",
        "page": page,
        "product": product,
        "steps": steps,
    }


def create_apple_search_accessories_task(
    product: str,
) -> dict:
    steps = [
        "Go to https://www.apple.com",
        "Click on 'Accessories' in the main nav",
        f"Click the search field labelled 'Search accessories' and type in '{product}' then hit Enter",
        "Once on the search results page, scroll down until the first product is visible",
        "Exit",
    ]
    return {
        "task_type": "apple_search_accessories",
        "product": product,
        "steps": steps,
    }


def create_apple_sort_accessories_task(
    product: str,
    sort_by: Literal["Relevancy", "Popularity", "Newest",
                     "Price: Low to High", "Price: High to Low"] | None = None
) -> dict:
    if sort_by is None:
        sort_by = random.choice(SORT_BY)
    task = create_apple_search_accessories_task(product)
    task["sort_by"] = sort_by
    task["steps"].insert(
        3,
        f"Click on the 'Sort by' dropdown and select '{sort_by}'"
    )
    task["task_type"] = "apple_sort_accessories"
    return task


def create_apple_basic_goto_page_task(
    page: Literal[
        "Store", "Mac", "iPad", "iPhone", "Watch",
        "Vision", "AirPods", "TV & Home", "Entertainment",
        "Accessories", "Support"
    ]
) -> dict:
    steps = [
        "Go to https://www.apple.com",
        f"Click on '{page}' in the top navigation",
        "Exit",
    ]
    return {
        "task_type": "apple_navigate_page",
        "page": page,
        "steps": steps,
    }


def create_apple_basic_support_task(
    basic_support_item: str | None = None
) -> dict:
    if basic_support_item is None:
        basic_support_item = random.choice(BASIC_SUPPORT_ITEMS)

    steps = [
        "Go to https://www.apple.com",
        "Click on 'Support' in the top nav",
        "Scroll down to the 'Apple Support' section, until the device options are visible",
        f"Click on the '{basic_support_item}' button",
        "Exit",
    ]
    return {
        "task_type": "apple_support",
        "product": basic_support_item,
        "steps": steps,
    }


def create_apple_find_store_locator_task() -> dict:
    steps = [
        "Go to https://www.apple.com",
        "Scroll down to the bottom of the page and click 'Find a Store' in the footer of the page",
    ]
    if random.random() < 0.5:
        steps.append(
            "Click the 'Use current location' button to find stores near you"
        )
    else:
        faker = Faker()
        random_zip = faker.zipcode()
        steps.extend([
            f"Click the 'Search by location, ZIP, or store name' field and type in '{random_zip}'",
            "Press Enter to search",
            "Click on the first result in the store locator results list",
        ])
    steps.append("Exit")
    return {
        "task_type": "apple_find_store_locator",
        "steps": steps,
    }


def create_apple_support_qa_task(product: str) -> dict:
    class SupportQuestion(BaseModel):
        question: str = Field(
            description=f"Factual question you'd search on support.apple.com about '{product}'"
        )

    @ell.complex(model="gpt-4o", response_format=SupportQuestion)
    def lmp(product: str):
        return [
            ell.user(
                f"Generate one concise factual question you would answer on Apple.com about '{product}'. "
                "A good for example 'iPhone' is 'how do I restore my iPhone from a backup'."
            )
        ]

    question = lmp(product).parsed.question  # type: ignore

    steps = [
        "Go to https://www.apple.com",
        f"Click on the 'Support' button in the top navigation bar",
        "Scroll down until the 'Search support' field is visible",
        f"Click the search icon and type in '{question}' and press Enter",
        "On the results page, scroll down until you find the result that best answers the question and click on that result",
        "Exit",
    ]
    return {
        "task_type": "apple_support_qa",
        "product": product,
        "question": question,
        "steps": steps,
    }


def create_apple_tech_specs_task(page: str, product: str) -> dict:
    steps = [
        "Go to https://www.apple.com",
        f"Click on '{page}' in the top navigation",
        f"Click on '{product}' in the list of products directly below the top navigation bar",
        "Scroll down to until the 'Tech Specs' button in the header becomes visible",
        "Click on the 'Tech Specs' button",
        "Exit",
    ]
    return {
        "task_type": "apple_tech_specs",
        "page": page,
        "product": product,
        "steps": steps,
    }


def create_apple_tech_specs_qa_task(
    page: str, product: str
) -> dict:
    class TechSpecsQuestion(BaseModel):
        question: str = Field(
            description=f"Factual question you'd search on Apple.com about '{product}'"
        )

    @ell.complex(model="gpt-4o", response_format=TechSpecsQuestion)
    def lmp(page: str, product: str):
        return [
            ell.user(
                f"Generate one concise factual question you would answer on Apple.com about '{product}' in the 'Tech Specs' section. "
                "A good example for 'iPhone 16 Pro' is 'What is the battery life of the iPhone 16 Pro?'"
            )
        ]

    question = lmp(page, product).parsed.question  # type: ignore

    steps = [
        "Go to https://www.apple.com",
        f"Click on '{page}' in the top navigation",
        f"Click on '{product}' in the list of products directly below the top navigation bar",
        "Scroll down to until the 'Tech Specs' button in the header becomes visible",
        "Click on the 'Tech Specs' button",
        f"Scroll down to the 'Tech Specs' until the section that best answers '{question}' is visible",
        "Exit",
    ]

    return {
        "task_type": "apple_tech_specs_qa",
        "page": page,
        "product": product,
        "question": question,
        "steps": steps,
    }


def generate_apple_task(
    task_type: Literal[
        "apple_check_price",
        "apple_search_accessories",
        "apple_navigate_page",
        "apple_sort_accessories",
        "apple_support",
        "apple_find_store_locator",
        "apple_qa",
        "apple_support_qa",
        "apple_tech_specs",
        "apple_tech_specs_qa",
    ],
    product: str | None = None,
    page: str | None = None
) -> dict:

    if product is None:
        page = random.choice(list(PRODUCTS.keys()))
        product = random.choice(PRODUCTS[page])

    if page is None:
        page = random.choice(PAGES)

    func = TASK_FUNCS.get(task_type, None)
    if not func:
        raise NotImplementedError(
            f"Unknown task_type: {task_type}, available: {list(TASK_FUNCS.keys())}")

    sig = inspect.signature(func)
    kwargs = {}
    if "product" in sig.parameters:
        kwargs["product"] = product
    if "page" in sig.parameters:
        kwargs["page"] = page

    task = func(**kwargs)
    task["instruction"] = get_instruction("google_search", task["steps"]).model_dump()
    return task


TASK_FUNCS: dict[str, callable] = {
    "apple_check_price": create_apple_check_price_task,
    "apple_search_accessories": create_apple_search_accessories_task,
    "apple_navigate_page": create_apple_basic_goto_page_task,
    "apple_sort_accessories": create_apple_sort_accessories_task,
    "apple_support": create_apple_basic_support_task,
    "apple_find_store_locator": create_apple_find_store_locator_task,
    "apple_qa": create_apple_qa_task,
    "apple_support_qa": create_apple_support_qa_task,
    "apple_tech_specs": create_apple_tech_specs_task,
    "apple_tech_specs_qa": create_apple_tech_specs_qa_task,
}
APPLE_TASK_TYPES = TASK_FUNCS.keys()


if __name__ == '__main__':
    tasks = {}
    tasks_to_run = APPLE_TASK_TYPES

    for task_type in tasks_to_run:
        tasks[task_type] = generate_apple_task(
            task_type,
        )
        print(f"task type: {task_type} = {tasks[task_type]}")

    import ipdb
    ipdb.set_trace()
