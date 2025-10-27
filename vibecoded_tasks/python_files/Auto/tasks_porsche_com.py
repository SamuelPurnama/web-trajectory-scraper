import json, random
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

PORSCHE_TASK_TYPES = Literal[
    "porsche_model_overview",
    "porsche_compare_models",
    "porsche_locate_dealer",
    "porsche_schedule_test_drive",
    "porsche_explore_accessories",
    "porsche_view_special_offers",
    "porsche_request_brochure",
]

PORSCHE_SAMPLING_CONFIG: Dict[PORSCHE_TASK_TYPES, int] = {
    "porsche_model_overview": 10,
    "porsche_compare_models": 10,
    "porsche_locate_dealer": 10,
    "porsche_schedule_test_drive": 10,
    "porsche_explore_accessories": 10,
    "porsche_view_special_offers": 10,
    "porsche_request_brochure": 10,
}

PORSCHE_MODELS = [
    "Taycan", "911", "718", "Panamera", "Macan", "Cayenne"
]

URLS = {
    "Taycan": "https://www.porsche.com/usa/models/taycan/taycan-models/taycan/",
    "911": "https://www.porsche.com/usa/models/911",
    "718": "https://www.porsche.com/usa/models/718",
    "Panamera": "https://www.porsche.com/usa/models/panamera",
    "Macan": "https://www.porsche.com/usa/models/macan",
    "Cayenne": "https://www.porsche.com/usa/models/cayenne",
}

def _ui() -> list[str]:
    return ["Dismiss popups/cookies if shown.", "Do not submit personal info; only browse/read."]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Porsche.com", steps).model_dump()

def _go_home() -> list[str]:
    return ["Go to url 'https://www.porsche.com/'.", *_ui()]

def porsche_model_overview(payload: dict) -> dict:
    model = payload.get("model", random.choice(PORSCHE_MODELS))
    url = URLS[model]
    steps = [
        f"Go to model page '{url}'.",
        *_ui(),
        "Explore the overview section.",
        "Record the base price, top speed, and 0-60 mph acceleration time."
    ]
    return {"task_type": "porsche_model_overview", "model": model, "steps": steps}

def porsche_compare_models(payload: dict) -> dict:
    model_a = payload.get("modelA", random.choice(PORSCHE_MODELS))
    model_b = payload.get("modelB", random.choice([m for m in PORSCHE_MODELS if m != model_a]))
    steps = _go_home() + [
        "Navigate to 'Compare Models' section.",
        f"Select model A as '{model_a}'.",
        f"Select model B as '{model_b}'.",
        "Compare specifications such as horsepower, torque, and fuel economy.",
        "Note two key differences between the models."
    ]
    return {"task_type": "porsche_compare_models", "modelA": model_a, "modelB": model_b, "steps": steps}

def porsche_locate_dealer(payload: dict) -> dict:
    steps = _go_home() + [
        "Go to 'Find a Dealer' page.",
        "Enter a city or ZIP code '10001'.",
        "Select the nearest dealer from the list.",
        "Record dealer's name, location, and contact information."
    ]
    return {"task_type": "porsche_locate_dealer", "steps": steps}

def porsche_schedule_test_drive(payload: dict) -> dict:
    model = payload.get("model", random.choice(PORSCHE_MODELS))
    steps = _go_home() + [
        "Navigate to 'Schedule a Test Drive' section.",
        f"Select model '{model}'.",
        "Choose a dealer from available options.",
        "Fill in the test drive request form, ensure no personal data is used."
    ]
    return {"task_type": "porsche_schedule_test_drive", "model": model, "steps": steps}

def porsche_explore_accessories(payload: dict) -> dict:
    model = payload.get("model", random.choice(PORSCHE_MODELS))
    steps = _go_home() + [
        f"Navigate to '{model}' model page.",
        "Go to 'Accessories' section.",
        "Browse through available accessories.",
        "Select an accessory and view its details including price and compatibility."
    ]
    return {"task_type": "porsche_explore_accessories", "model": model, "steps": steps}

def porsche_view_special_offers(_: dict) -> dict:
    steps = _go_home() + [
        "Go to 'Special Offers' page.",
        "Identify any available promotions or deals.",
        "Record offer details including model, offer type, and expiration date if available."
    ]
    return {"task_type": "porsche_view_special_offers", "steps": steps}

def porsche_request_brochure(payload: dict) -> dict:
    model = payload.get("model", random.choice(PORSCHE_MODELS))
    steps = _go_home() + [
        "Navigate to 'Request a Brochure' section.",
        f"Select model '{model}'.",
        "Follow steps to request a brochure, ensuring no personal info is entered."
    ]
    return {"task_type": "porsche_request_brochure", "model": model, "steps": steps}

_TASK_GENERATORS: Dict[PORSCHE_TASK_TYPES, Callable[[dict], dict]] = {
    "porsche_model_overview": porsche_model_overview,
    "porsche_compare_models": porsche_compare_models,
    "porsche_locate_dealer": porsche_locate_dealer,
    "porsche_schedule_test_drive": porsche_schedule_test_drive,
    "porsche_explore_accessories": porsche_explore_accessories,
    "porsche_view_special_offers": porsche_view_special_offers,
    "porsche_request_brochure": porsche_request_brochure,
}

def generate_porsche_task(task_type: PORSCHE_TASK_TYPES, payload: dict) -> dict:
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
    items = list(PORSCHE_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_porsche_task, ttype, p))
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