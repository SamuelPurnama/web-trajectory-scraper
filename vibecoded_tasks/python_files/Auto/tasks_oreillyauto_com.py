import json
import random
from typing import Callable, Dict, Literal
from concurrent.futures import ThreadPoolExecutor, as_completed
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

OREILLY_TASK_TYPES = Literal[
    "search_product",
    "view_cart",
    "apply_coupon",
    "find_repair_shop",
    "explore_promotions",
    "create_account",
    "sign_in",
    "navigate_customer_service",
    "view_terms_conditions",
    "discover_payment_options"
]

OREILLY_SAMPLING_CONFIG: Dict[OREILLY_TASK_TYPES, int] = {
    "search_product": 10,
    "view_cart": 10,
    "apply_coupon": 10,
    "find_repair_shop": 10,
    "explore_promotions": 10,
    "create_account": 10,
    "sign_in": 10,
    "navigate_customer_service": 10,
    "view_terms_conditions": 10,
    "discover_payment_options": 10
}

COUPONS = ["OCT15", "WELCOME10", "SAVE20"]
PRODUCTS = ["brake pad", "oil filter", "wiper blade", "headlight", "spark plug"]
REPAIR_KEYWORDS = ["tire", "brake", "engine", "battery", "oil change"]
USERNAMES = ["user_example", "sample_name"]
PASSWORD = "Password123!"
PROMOS = ["Current Ad", "15% OFF $75+", "Rain-X Wiper Blades"]
LOCATIONS = ["Los Angeles, CA", "Chicago, IL", "Houston, TX", "Phoenix, AZ", "Philadelphia, PA"]

def _instr(steps: list[str]) -> dict:
    return get_instruction("O'Reilly Auto Parts", steps).model_dump()

def search_product(_: dict) -> dict:
    product = random.choice(PRODUCTS)
    steps = [
        "Go to url 'https://www.oreillyauto.com'.",
        "Dismiss any pop-ups that may appear.",
        f"Search for '{product}' using the site search bar.",
        "Confirm the results page displays products related to the search term."
    ]
    return {"task_type": "search_product", "product": product, "steps": steps}

def view_cart(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.oreillyauto.com'.",
        "Dismiss any pop-ups that may appear.",
        "Click on the 'Cart' icon.",
        "Confirm the cart page loads and displays its contents."
    ]
    return {"task_type": "view_cart", "steps": steps}

def apply_coupon(_: dict) -> dict:
    coupon = random.choice(COUPONS)
    steps = [
        "Go to url 'https://www.oreillyauto.com'.",
        "Dismiss any pop-ups that may appear.",
        "Navigate to the 'Current Ad' or 'Promotions' page.",
        f"Find and apply the coupon code '{coupon}' at checkout.",
        "Confirm the discount is applied to the order total."
    ]
    return {"task_type": "apply_coupon", "coupon": coupon, "steps": steps}

def find_repair_shop(_: dict) -> dict:
    location = random.choice(LOCATIONS)
    keyword = random.choice(REPAIR_KEYWORDS)
    steps = [
        "Go to url 'https://findashop.oreillyauto.com/home'.",
        "Dismiss any pop-ups that may appear.",
        f"Search for repair shops in '{location}' using the keyword '{keyword}'.",
        "Confirm the search results display repair shops relevant to the query."
    ]
    return {"task_type": "find_repair_shop", "location": location, "keyword": keyword, "steps": steps}

def explore_promotions(_: dict) -> dict:
    promo = random.choice(PROMOS)
    steps = [
        f"Go to url 'https://www.oreillyauto.com'.",
        "Dismiss any pop-ups that may appear.",
        f"Navigate to the promotions section and explore the offer '{promo}'.",
        "Verify the details of the promotion are correct and visible."
    ]
    return {"task_type": "explore_promotions", "promo": promo, "steps": steps}

def create_account(_: dict) -> dict:
    username = random.choice(USERNAMES)
    steps = [
        "Go to url 'https://www.oreillyauto.com/create-account'.",
        "Dismiss any pop-ups that may appear.",
        f"Enter a valid username '{username}', password, and other required details for account creation.",
        "Submit the form and confirm account creation is successful."
    ]
    return {"task_type": "create_account", "username": username, "steps": steps}

def sign_in(_: dict) -> dict:
    username = random.choice(USERNAMES)
    steps = [
        "Go to url 'https://www.oreillyauto.com/signin?successUrl=/'.",
        "Dismiss any pop-ups that may appear.",
        f"Enter username '{username}' and password.",
        "Submit the form and confirm sign in with a welcome message."
    ]
    return {"task_type": "sign_in", "username": username, "steps": steps}

def navigate_customer_service(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.oreillyauto.com'.",
        "Dismiss any pop-ups that may appear.",
        "Navigate to the 'Contact Us' or 'Customer Service' section.",
        "Confirm the customer service contact options are visible."
    ]
    return {"task_type": "navigate_customer_service", "steps": steps}

def view_terms_conditions(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.oreillyauto.com'.",
        "Dismiss any pop-ups that may appear.",
        "Scroll to the bottom and click 'Terms of Use'.",
        "Confirm that the terms and conditions page loads and the content is readable."
    ]
    return {"task_type": "view_terms_conditions", "steps": steps}

def discover_payment_options(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.oreillyauto.com'.",
        "Dismiss any pop-ups that may appear.",
        "Navigate to the payment or checkout section.",
        "Verify the available payment methods such as credit card, PayPal, and 'Buy Now, Pay Later'."
    ]
    return {"task_type": "discover_payment_options", "steps": steps}

_TASK_GENERATORS: Dict[OREILLY_TASK_TYPES, Callable[[dict], dict]] = {
    "search_product": search_product,
    "view_cart": view_cart,
    "apply_coupon": apply_coupon,
    "find_repair_shop": find_repair_shop,
    "explore_promotions": explore_promotions,
    "create_account": create_account,
    "sign_in": sign_in,
    "navigate_customer_service": navigate_customer_service,
    "view_terms_conditions": view_terms_conditions,
    "discover_payment_options": discover_payment_options
}

def generate_oreilly_task(task_type: OREILLY_TASK_TYPES, payload: dict) -> dict:
    task = _TASK_GENERATORS[task_type](payload or {})
    task["instruction"] = _instr(task["steps"])
    return task

def main(filepath: str, payloads_json: str = "", num_workers: int = 12, timeout: int = 60, seed: int = 42, indent: int = 2):
    payloads = []
    if payloads_json:
        with open(payloads_json) as f:
            payloads = json.load(f)
    if not isinstance(payloads, list): payloads = []
    random.seed(seed)
    futures, out = [], []
    items = list(OREILLY_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_oreilly_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)