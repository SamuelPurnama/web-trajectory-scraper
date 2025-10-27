import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

CARS_TASK_TYPES = Literal[
    "car_search_and_read_review",
    "compare_car_models",
    "explore_expert_recommendations",
    "subscribe_newsletter",
    "watch_latest_car_videos",
    "explore_car_photos",
    "browse_latest_car_news"
]

CARS_SAMPLING_CONFIG: Dict[CARS_TASK_TYPES, int] = {
    "car_search_and_read_review": 10,
    "compare_car_models": 10,
    "explore_expert_recommendations": 10,
    "subscribe_newsletter": 10,
    "watch_latest_car_videos": 10,
    "explore_car_photos": 10,
    "browse_latest_car_news": 10,
}

CARS = [
    "Tesla Model 3","Tesla Model Y","BMW i3","BMW 3 Series","Mercedes-Benz CLA","Mercedes-Benz C-Class",
    "Toyota Prius","Toyota Camry","Toyota Corolla","Toyota RAV4","Toyota Highlander","Toyota 4Runner",
    "Honda Civic","Honda Accord","Honda CR-V","Subaru Outback","Subaru Forester","Ford F-150","Ford Mustang",
    "Chevrolet Bolt EUV","Chevrolet Silverado 1500","Nissan Leaf","Nissan Rogue","Hyundai Ioniq 5","Hyundai Elantra",
    "Kia Niro","Kia Sportage","Volkswagen Golf","Volvo XC60","Audi A4","Mazda CX-5","Porsche Macan"
]

def _ui() -> list[str]:
    return ["Dismiss popups/cookies if shown.", "Do not submit personal info; only browse/read."]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Car and Driver", steps).model_dump()

def car_search_and_read_review(payload: dict) -> dict:
    car = payload.get("car", random.choice(CARS))
    steps = [
        "Go to url 'https://www.caranddriver.com/'.",
        *_ui(),
        f"Search for car review of '{car}'.",
        "Open the review page from the first result.",
        "Read and note down any two features or reviews mentioned."
    ]
    return {"task_type": "car_search_and_read_review", "car": car, "steps": steps}

def compare_car_models(payload: dict) -> dict:
    car1, car2 = random.sample(CARS, 2)
    steps = [
        "Go to url 'https://www.caranddriver.com/compare/'.",
        *_ui(),
        f"Select '{car1}' and '{car2}' models for comparison.",
        "Note down any two differences such as specs, ratings or features."
    ]
    return {"task_type": "compare_car_models", "model1": car1, "model2": car2, "steps": steps}

def explore_expert_recommendations(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.caranddriver.com/buying-guide/'.",
        *_ui(),
        "Explore expert recommended car buying guides.",
        "Read any guide that interests you and note any highlighted points."
    ]
    return {"task_type": "explore_expert_recommendations", "steps": steps}

def subscribe_newsletter(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.caranddriver.com/email/caranddriver-newsletter'.",
        *_ui(),
        "Follow the link to sign up for the newsletter.",
        "Make sure no personal information is entered beyond browsing/reading."
    ]
    return {"task_type": "subscribe_newsletter", "steps": steps}

def watch_latest_car_videos(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.caranddriver.com/videos/'.",
        *_ui(),
        "Watch the latest video by browsing through the video list.",
        "Note any two highlighted car features or announcements from the video."
    ]
    return {"task_type": "watch_latest_car_videos", "steps": steps}

def explore_car_photos(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.caranddriver.com/photos/'.",
        *_ui(),
        "Browse through the latest car photo galleries.",
        "Select a gallery and note any two cars or features you found interesting."
    ]
    return {"task_type": "explore_car_photos", "steps": steps}

def browse_latest_car_news(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.caranddriver.com/news/'.",
        *_ui(),
        "Browse the latest car news articles.",
        "Open an article of interest and summarize two key points in it."
    ]
    return {"task_type": "browse_latest_car_news", "steps": steps}

_TASK_GENERATORS: Dict[CARS_TASK_TYPES, Callable[[dict], dict]] = {
    "car_search_and_read_review": car_search_and_read_review,
    "compare_car_models": compare_car_models,
    "explore_expert_recommendations": explore_expert_recommendations,
    "subscribe_newsletter": subscribe_newsletter,
    "watch_latest_car_videos": watch_latest_car_videos,
    "explore_car_photos": explore_car_photos,
    "browse_latest_car_news": browse_latest_car_news,
}

def generate_task(task_type: CARS_TASK_TYPES, payload: dict) -> dict:
    t = _TASK_GENERATORS[task_type](payload or {})
    t["instruction"] = _instr(t["steps"])
    return t

def main(filepath: str, payloads_json: str = "", num_workers: int = 12, timeout: int = 60, seed: int = 42, indent: int = 2):
    payloads = []
    if payloads_json:
        with open(payloads_json) as f:
            payloads = json.load(f)
    if not isinstance(payloads, list): payloads = []
    random.seed(seed)
    futures, out = [], []
    items = list(CARS_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try:
                out.append(fut.result(timeout=timeout))
            except Exception:
                pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)