import json, random
from typing import Callable, Dict, Literal
from concurrent.futures import ThreadPoolExecutor, as_completed
import fire
from tasks.instruction_utils import get_instruction
from tqdm import tqdm

AUTOV_EVOLUTION_TASK_TYPES = Literal[
    "news_browse_headlines",
    "cars_find_vehicle_details",
    "compare_motorcycles",
    "bun_get_spy_shot_article",
    "green_technology_focus",
    "auto_glossary_search",
    "check_editorial_for_keyword"
]

AUTOEVOLUTION_SAMPLING_CONFIG: Dict[AUTOV_EVOLUTION_TASK_TYPES, int] = {
    "news_browse_headlines": 10,
    "cars_find_vehicle_details": 10,
    "compare_motorcycles": 10,
    "bun_get_spy_shot_article": 10,
    "green_technology_focus": 10,
    "auto_glossary_search": 10,
    "check_editorial_for_keyword": 10
}

VEHICLE_MODELS = [
    "Toyota GR Corolla", "Mercedes-Benz SL Roadster", "Nissan Sentra",
    "MG U9", "MITSUBISHI Eclipse Cross", "FERRARI Testarossa Spider"
]

MOTORCYCLES = [
    "YAMAHA XSR900", "YAMAHA NMAX 125", "YAMAHA RayZR",
    "YAMAHA Tricity 125", "YAMAHA XMAX 125"
]

GLOSSARY_TERMS = ["ABS", "Turbocharger", "EV battery", "AWD", "Multilink suspension"]

KEYWORDS = ["performance", "electric", "hybrid", "luxury", "concept"]

def _ui() -> list[str]:
    return ["Avoid subscribing to newsletters or accepting cookies.", 
            "Explore featured content without leaving personal information."]

def _instr(steps: list[str]) -> dict:
    return get_instruction("auto-evolution.com", steps).model_dump()

def _go_home() -> list[str]:
    return ["Go to url 'https://www.autoevolution.com/'.", *_ui()]

def news_browse_headlines(payload: dict) -> dict:
    steps = _go_home() + [
        "Click on 'News' to explore the latest articles.",
        "Read through the headlines.",
        "Select an article.",
        "Verify the date of publication is recent and contains a summary related to cars.",
    ]
    return {"task_type": "news_browse_headlines", "steps": steps}

def cars_find_vehicle_details(payload: dict) -> dict:
    model = payload.get("model", random.choice(VEHICLE_MODELS))
    steps = _go_home() + [
        "Navigate to 'Cars Database'.",
        f"Look up the vehicle model '{model}'.",
        "Confirm the specifications include engine size and top speed."
    ]
    return {"task_type": "cars_find_vehicle_details", "model": model, "steps": steps}

def compare_motorcycles(payload: dict) -> dict:
    motorcycles = random.sample(MOTORCYCLES, 2)
    steps = _go_home() + [
        "Navigate to 'Moto Database'.",
        f"Search and select '{motorcycles[0]}'.",
        f"Search and select '{motorcycles[1]}'.",
        "List two key differences in performance metrics like engine and horsepower."
    ]
    return {"task_type": "compare_motorcycles", "motorcycles": motorcycles, "steps": steps}

def bun_get_spy_shot_article(_: dict) -> dict:
    steps = _go_home() + [
        "Click on 'Spyshots' in the navigation.",
        "Open any recent article containing spy photos.",
        "Validate the presence of clear vehicle shots and discuss the predicted model attributes."
    ]
    return {"task_type": "bun_get_spy_shot_article", "steps": steps}

def green_technology_focus(_: dict) -> dict:
    steps = _go_home() + [
        "Select 'EV/Hybrids'.",
        "Browse to find an article focused on new green technology.",
        "Verify if the article details advancements in electric vehicle range or efficiency."
    ]
    return {"task_type": "green_technology_focus", "steps": steps}

def auto_glossary_search(payload: dict) -> dict:
    term = payload.get("term", random.choice(GLOSSARY_TERMS))
    steps = _go_home() + [
        "Click on 'Glossary of automotive terms'.",
        f"Search for the term '{term}'.",
        "Read the explanation and ensure it corresponds to the search term."
    ]
    return {"task_type": "auto_glossary_search", "term": term, "steps": steps}

def check_editorial_for_keyword(payload: dict) -> dict:
    keyword = payload.get("keyword", random.choice(KEYWORDS))
    steps = _go_home() + [
        "Go to the 'Editorial' section.",
        f"Search for the keyword '{keyword}'.",
        "Confirm at least one result is found with the keyword in its title or summary."
    ]
    return {"task_type": "check_editorial_for_keyword", "keyword": keyword, "steps": steps}

_TASK_GENERATORS: Dict[AUTOV_EVOLUTION_TASK_TYPES, Callable[[dict], dict]] = {
    "news_browse_headlines": news_browse_headlines,
    "cars_find_vehicle_details": cars_find_vehicle_details,
    "compare_motorcycles": compare_motorcycles,
    "bun_get_spy_shot_article": bun_get_spy_shot_article,
    "green_technology_focus": green_technology_focus,
    "auto_glossary_search": auto_glossary_search,
    "check_editorial_for_keyword": check_editorial_for_keyword,
}

def generate_autoevolution_task(task_type: AUTOV_EVOLUTION_TASK_TYPES, payload: dict) -> dict:
    t = _TASK_GENERATORS[task_type](payload or {})
    t["instruction"] = _instr(t["steps"])
    return t

def main(filepath: str, payloads_json: str = "", num_workers: int = 12, 
         timeout: int = 60, seed: int = 42, indent: int = 2):

    payloads = []
    if payloads_json:
        with open(payloads_json) as f:
            payloads = json.load(f)
    if not isinstance(payloads, list):
        payloads = []

    random.seed(seed)
    futures, out = [], []
    items = list(AUTOEVOLUTION_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_autoevolution_task, ttype, p))
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