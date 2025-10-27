import json
import random
from typing import Literal
from tasks.amazon.constants import AMAZON_KEYWORDS, PRODUCT_SORT_CRITERIA, DEPARTMENT_CATEGORIES
from tasks.instruction_utils import get_instruction


def find_products_on_amazon_by_keyword(keyword: str):
    steps = [
        "Go to https://www.amazon.com unless already on it with the search box visible.",
        f"Search '{keyword}' using the search box. The products related to {keyword} should be visible in the search results.",
    ]

    return [
        dict(
            task_type="find_products_on_amazon_by_keyword",
            keyword=keyword,
            steps=steps,
        )
    ]


def find_products_on_amazon_by_keyword_with_free_shipping(keyword: str):
    task = find_products_on_amazon_by_keyword(keyword)[0] 
    task["steps"] += [  # pyright: ignore
        "Once the search results are displayed, look for the checkbox for 'Eligible for Free Shipping' on the left.",
    ]
    task["steps"].append(
        f"The products related to '{keyword}' that are eligible for free shipping should be visible in the search results."
    )
    return [
        dict(
            task_type="find_products_on_amazon_by_keyword_with_free_shipping",
            keyword=keyword,
            steps=task["steps"],
        )
    ]


def find_products_on_amazon_by_keyword_within_a_price_range(keyword: str, min_price: float = None, max_price: float = None):
    task = find_products_on_amazon_by_keyword(keyword)[0] 
    task["steps"] += [  # pyright: ignore
        "Once the search results are displayed, look for the filter options on the left side of the page.",
    ]
    if min_price is not None:
        task["steps"].append(f"Set the minimum price to ${min_price}.")
    if max_price is not None:
        task["steps"].append(f"Set the maximum price to ${max_price}.")
    task["steps"].append(
        f"The products related to '{keyword}' should be visible in the search results, filtered by the specified price range."
    )
    return [
        dict(
            task_type="find_products_on_amazon_by_keyword_within_a_price_range",
            keyword=keyword,
            min_price=min_price,
            max_price=max_price,
            steps=task["steps"],
        )
    ]


def find_products_on_amazon_by_keyword_sort_by_criteria(
    keyword: str, sort_criteria: str = "featured"
):
    task = find_products_on_amazon_by_keyword(keyword)[0] 
    task["steps"] += [  # pyright: ignore
        "Once the search results are displayed, look for the 'Sort by' option, usually located at the top of the search results.",
        f"Click on 'Sort by' and sort the products by '{sort_criteria}'. The products related to '{keyword}' should be visible and sorted by '{sort_criteria}'.",
    ]
    steps = task["steps"]  
    return [
        dict(
            task_type="find_products_on_amazon_by_keyword_sort_by_criteria",
            keyword=keyword,
            sort_criteria=sort_criteria,
            steps=steps,
        )
    ]


def go_to_top_product_detail_page(keyword: str, sort_criteria: str = "featured"):
    task = find_products_on_amazon_by_keyword_sort_by_criteria(keyword, sort_criteria)[0]
    task["steps"] += [  # pyright: ignore
        "Once the search results are displayed, look for the top product in the list.",
        "Click on the product to go to its detail page.",
    ]

    return [
        dict(
            task_type="go_to_top_product_detail_page",
            keyword=keyword,
            sort_criteria=sort_criteria,
            steps=task["steps"],
        )
    ]


# def find_product_on_amazon_by_name(product_name: str):
#     steps = [
#         "Go to https://www.amazon.com unless already on it with the search box visible.",
#         f"Search '{product_name}' using the search box.",
#         f"The product with name '{product_name}' should be visible in the search results.",
#         "Once the search results are displayed fully, look for the product in the list. If the product is not found in the first few results, scroll down the list of search results until you see it.",
#         "If there are multiple products with the same name, choose the first one.",
#         "If the product is not found, report to the user and ask if they want to go to the next page or try a different search term.",
#         "Once the product is found, click on it to go to its detail page."
#     ]

#     return [
#         dict(
#             task_type="find_product_on_amazon_by_name",
#             product_name=product_name,
#             steps=steps,
#         )
#     ]


# def summarize_product_details(product_name: str):
def summarize_product_details(keyword: str, sort_criteria: str = "featured"):
    task = go_to_top_product_detail_page(keyword, sort_criteria)[0]
    task["steps"] += [  # pyright: ignore
        "Once on the product detail page, look for the product price, description, specifications, and any other relevant details.",
        "Summarize the price, key features and specifications of the product.",
    ]

    return [
        dict(
            task_type="summarize_product_details",
            steps=task["steps"],
            keyword=keyword,
            sort_criteria=sort_criteria,
        )
    ]


# def summarize_product_reviews(product_name: str, num_reviews: int = 5):
def summarize_product_reviews(keyword: str, sort_criteria: str = "featured", num_reviews: int = 5):
    task = go_to_top_product_detail_page(keyword, sort_criteria)[0]
    task["steps"] += [  # pyright: ignore
        "Once on the product detail page, scroll down to the reviews section.",
        f"Look for the top {num_reviews} reviews of the product.",
        "Summarize the key points from these reviews, including both positive and negative aspects.",
    ]

    return [
        dict(
            task_type="summarize_product_reviews",
            num_reviews=num_reviews,
            steps=task["steps"],
            keyword=keyword,
            sort_criteria=sort_criteria,
        )
    ]


# def add_product_to_cart(product_name: str):
def add_product_to_cart(keyword: str, sort_criteria: str = "featured"):
    task = go_to_top_product_detail_page(keyword, sort_criteria)[0]
    
    task["steps"] += [  # pyright: ignore
        "Once on the product detail page, look for the 'Add to Cart' button.",
        "Click on the 'Add to Cart' button to add the product to your cart.",
    ]

    return [
        dict(
            task_type="add_product_to_cart",
            steps=task["steps"],
            keyword=keyword,
            sort_criteria=sort_criteria,
        )
    ]


def check_cart_for_products():
    steps = [
        "Go to the cart page by clicking on the cart icon or link.",
        "Check what products are currently in the cart, and report to the user a summary of the products in the cart.",
        "If the cart is empty, let the user know that there are no products in the cart.",
    ]
    return [
        dict(
            task_type="check_cart_for_products",
            steps=steps,
        )
    ]


def summarize_multiple_product_details(keyword: str, sort_criteria: str = "featured", num_products: int = 3):
    task = find_products_on_amazon_by_keyword_sort_by_criteria(keyword, sort_criteria)[0]
    task["steps"] += [  # pyright: ignore
        f"Once the search results are displayed, look for the top {num_products} products in the list.",
        f"For each of the top {num_products} products, go to its detail page and take note of the product details.",
        f"Summarize the key details of the {num_products} products, including price, features, and specifications.",
    ]
    tasks = [
        dict(
            task_type="summarize_multiple_product_details",
            keyword=keyword,
            sort_criteria=sort_criteria,
            num_products=num_products,
            steps=task["steps"],
        )
    ]
    return tasks


def summarize_multiple_product_reviews(keyword: str, sort_criteria: str = "featured", num_products: int = 3):
    task = find_products_on_amazon_by_keyword_sort_by_criteria(keyword, sort_criteria)[0]
    task["steps"] += [  # pyright: ignore
        f"Once the search results are displayed, look for the top {num_products} products in the list.",
        f"For each of the top {num_products} products, go to its detail page and take note of the product reviews."
        f"Summarize the key points from these reviews for the {num_products} products, including both positive and negative aspects.",
    ]
    tasks = [
        dict(
            task_type="summarize_multiple_product_reviews",
            keyword=keyword,
            sort_criteria=sort_criteria,
            num_products=num_products,
            steps=task["steps"],
        )
    ]
    return tasks


def add_multiple_products_to_cart(keyword: str, sort_criteria: str = "featured", num_products: int = 3):
    task = find_products_on_amazon_by_keyword_sort_by_criteria(keyword, sort_criteria)[0]
    task["steps"] += [  # pyright: ignore
        f"Once the search results are displayed, look for the top {num_products} products in the list.",
        f"For each of the top {num_products} products, click on the 'Add to Cart' button to add the product to your cart.",
    ]
    tasks = [
        dict(
            task_type="add_multiple_products_to_cart",
            keyword=keyword,
            sort_criteria=sort_criteria,
            num_products=num_products,
            steps=task["steps"],
        )
    ]
    return tasks


# def add_multiple_products_to_cart(product_names: list[str]):
#     task = add_product_to_cart(product_names[0])[0]
#     for product_name in product_names[1:]:
#         task["steps"].append(
#             f"Next, add the product '{product_name}' to the cart."
#         )
#     tasks = [
#         dict(
#             task_type="add_multiple_products_to_cart",
#             product_names=product_names,
#             steps=task["steps"],
#         )
#     ]
#     return tasks
    

# def add_products_to_cart_and_check_cart(product_names: list[str]):
def add_products_to_cart_and_check_cart(keyword: str, sort_criteria: str = "featured", num_products: int = 3):
    task = add_multiple_products_to_cart(keyword, sort_criteria, num_products)[0]
    task["steps"].append(
        "Finally, check the cart to see if all products have been added successfully."
    )

    check_cart_steps = check_cart_for_products()[0]["steps"]
    task["steps"].extend(check_cart_steps)  # pyright: ignore

    tasks = [
        dict(
            task_type="add_products_to_cart_and_check_cart",
            keyword=keyword,
            sort_criteria=sort_criteria,
            num_products=num_products,
            steps=task["steps"],
        )
    ]
    return tasks


def find_bestseller_in_category_via_left_entry(category: str):
    p = random.random()
    steps = [
        "Go to https://www.amazon.com unless already on it with the search box visible.",
        "Look for the 'Best Sellers' link in the top navigation bar, and click on it.",
        f"Once on the Best Sellers page, look for '{category}' on the left side of the page. You may need to scroll down to find it.",
        f"Click on '{category}' to view the top-selling products in that category.",
        f"Once you are on the '{category}' page, go to the page of the #1 best-selling product in that category.",
    ]

    if p < 0.5:
        steps.append(
            f"Add the #1 best-selling product in '{category}' to your cart."
        )
    return [
        dict(
            task_type="find_bestseller_in_category_via_left_entry",
            category=category,
            steps=steps,
        )
    ]


def find_bestseller_in_category_via_top_entry(category: str):
    p = random.random()
    steps = [
        "Go to https://www.amazon.com unless already on it with the search box visible.",
        "Find the 'All' dropdown menu in the top navigation bar, and click on it.",
        "Find 'Best Sellers' in the dropdown menu, and click on it.",
        f"Look for '{category}' in the list of departments, and click on it. You may need to scroll down to find it.",  
        f"Once you found '{category}', click on it to view the top-selling products in that category.",
        f"Once you are on the '{category}' page, go to the page of the #1 best-selling product in that category.",
    ]
    if p < 0.5:
        steps.append(
            f"Add the #1 best-selling product in '{category}' to your cart."
        )
    return [
        dict(
            task_type="find_bestseller_in_category_via_top_entry",
            category=category,
            steps=steps,
        )
    ]


# def generate_product_qa(product_name: str, product_details: str):
#     class QuestionAnswer(BaseModel):
#         question: str = Field(
#             description="Factual question about the product that can be answered based on the provided details."
#         )
#         answer: str = Field(
#             description="Answer to the question typically containing 1-5 words or at most 20 words."
#         )

#     @ell.complex(model="gpt-4o", response_format=QuestionAnswer)
#     def lmp():
#         return [
#             ell.system(f"You are a product expert"),
#             ell.user(
#                 f"Generate a factual question answer pair that is relevant to the following product details:\n\nProduct Name: {product_name}\n\nDetails: {product_details}\n\n## Guidelines\n\nQuestion should be such that the answer typically contains 1-5 words or at most 20 words. Make sure your question is relevant to the product and can be answered purely based on the details provided."
#             ),
#         ]

#     qa: QuestionAnswer = lmp().parsed  # pyright: ignore
#     return qa.question, qa.answer


# def product_qa(product_name: str, product_details: str):
#     question, answer = generate_product_qa(product_name, product_details)
#     task = find_product_on_amazon_by_name(product_name)[0]
#     task["question"] = question
#     task["answer"] = answer
#     task["steps"].append(  # pyright: ignore
#         f"Once the product detail page is open, answer the following question based on the product details - '{question}'"
#     )
#     task["summary"] = product_details
#     task["task_type"] = "product_qa"
#     return [task]


def generate_amazon_task(
    task_type: Literal[
        "find_products_on_amazon_by_keyword",
        "find_products_on_amazon_by_keyword_sort_by_criteria",
        "find_products_on_amazon_by_keyword_within_a_price_range",
        "find_products_on_amazon_by_keyword_with_free_shipping",
        "go_to_top_product_detail_page",
        "summarize_product_details",
        "summarize_product_reviews",
        "add_product_to_cart",
        "check_cart_for_products",
        "add_multiple_products_to_cart",
        "add_products_to_cart_and_check_cart",
        "find_bestseller_in_category",
    ],
    keyword: str = None,
    sort_criteria: str = None,
    category: str = None,
):
    task_function = globals()[task_type]
    if task_type in [
        "find_products_on_amazon_by_keyword", 
        "find_products_on_amazon_by_keyword_with_free_shipping",
    ]:
        tasks = task_function(
            keyword=keyword,
        )
    elif task_type in ["find_products_on_amazon_by_keyword_within_a_price_range",]:
        if random.random() < 0.5:
            min_price = random.randint(10, 50)
        else:
            min_price = None
        if random.random() < 0.5:
            if min_price is not None:
                max_price = random.randint(min_price + 1, min_price + 500)
            else:
                max_price = random.randint(50, 500)
        else:
            max_price = None
        tasks = task_function(
            keyword=keyword,
            min_price=min_price,
            max_price=max_price,
        )
    elif task_type in ["check_cart_for_products"]:
        tasks = task_function()
    elif task_type in ["find_bestseller_in_category_via_left_entry", "find_bestseller_in_category_via_top_entry"]:
        tasks = task_function(category=category,)
    
    else:
        tasks = task_function(
            keyword=keyword,
            sort_criteria=sort_criteria,
        )

    for task in tasks:
        task["instruction"] = get_instruction(
            "amazon", task["steps"]
        ).model_dump()

    return tasks

if __name__ == "__main__":
    for task_type in [
        # "find_products_on_amazon_by_keyword",
        # "find_products_on_amazon_by_keyword_within_a_price_range",
        # "find_products_on_amazon_by_keyword_sort_by_criteria",
        # "go_to_top_product_detail_page",
        # # "find_product_on_amazon_by_name",
        # "summarize_product_details",
        # "summarize_product_reviews",
        # "add_product_to_cart",
        # "check_cart_for_products",
        # "add_multiple_products_to_cart",
        # "add_products_to_cart_and_check_cart",
        "find_bestseller_in_category",
        # "product_qa",
    ]:  
        keyword = random.choice(AMAZON_KEYWORDS)
        sort_criteria = random.choice(PRODUCT_SORT_CRITERIA)
        category = random.choice(DEPARTMENT_CATEGORIES)

        print(f"\n========== Task type: {task_type} ============")
        print(f"Keyword: {keyword}, Sort Criteria: {sort_criteria}")
        res = generate_amazon_task(
            task_type=task_type,
            keyword=keyword,
            sort_criteria=sort_criteria,
            category=category,
        )
        print(res)



