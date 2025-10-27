import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

HGTV_TASK_TYPES = Literal[
    "hgtv_accept_privacy_modal",
    "hgtv_open_terms_of_use",
    "hgtv_open_privacy_policy",
    "hgtv_modal_negative_no_accept",
    "hgtv_modal_link_navigation",
    "hgtv_modal_repeat_accept",
    "hgtv_modal_multi_tab_terms",
    "hgtv_modal_multi_tab_privacy",
    "hgtv_modal_link_keyboard",
    "hgtv_modal_accessibility_focus",
]

HGTV_SAMPLING_CONFIG: Dict[HGTV_TASK_TYPES, int] = {
    "hgtv_accept_privacy_modal": 10,
    "hgtv_open_terms_of_use": 10,
    "hgtv_open_privacy_policy": 10,
    "hgtv_modal_negative_no_accept": 10,
    "hgtv_modal_link_navigation": 10,
    "hgtv_modal_repeat_accept": 10,
    "hgtv_modal_multi_tab_terms": 10,
    "hgtv_modal_multi_tab_privacy": 10,
    "hgtv_modal_link_keyboard": 10,
    "hgtv_modal_accessibility_focus": 10,
}

HGTV_MODAL_LINKS = [
    "Terms of Use",
    "Privacy Policy",
]

HGTV_MODAL_URLS = [
    "https://www.hgtv.com",
    "https://www.hgtv.com/decorating",
    "https://www.hgtv.com/how-to/home-improvement",
    "https://www.hgtv.com/shows",
    "https://www.hgtv.com/design",
    "https://www.hgtv.com/bathroom-design",
    "https://www.hgtv.com/kitchen-design",
    "https://www.hgtv.com/outdoors",
    "https://www.hgtv.com/remodel",
    "https://www.hgtv.com/landscaping",
    "https://www.hgtv.com/rooms/bedroom",
    "https://www.hgtv.com/rooms/living-room",
    "https://www.hgtv.com/rooms/dining-room",
    "https://www.hgtv.com/rooms/kids-room",
    "https://www.hgtv.com/rooms/home-office",
    "https://www.hgtv.com/rooms/laundry-room",
    "https://www.hgtv.com/rooms/garage",
    "https://www.hgtv.com/rooms/entryway",
    "https://www.hgtv.com/rooms/basement",
    "https://www.hgtv.com/rooms/attic",
    "https://www.hgtv.com/rooms/game-room",
    "https://www.hgtv.com/rooms/home-gym",
]

HGTV_MODAL_ACCEPT_LABELS = [
    "Accept terms and close the modal",
    "Agree",
    "Accept and Continue",
    "OK",
    "I Agree",
    "Accept",
    "Close",
    "Continue",
    "Accept Terms",
    "Accept Privacy Policy",
    "Accept All",
    "Accept Cookies",
    "Accept Terms of Use",
    "Accept and Close",
    "Accept and Proceed",
    "Accept & Close",
    "Accept & Continue",
    "Accept Policy",
    "Accept Consent",
    "Accept Agreement",
    "Accept Modal",
]

HGTV_MODAL_LINK_VARIANTS = [
    "Terms of Use",
    "terms of use",
    "TERMS OF USE",
    "Privacy Policy",
    "privacy policy",
    "PRIVACY POLICY",
    "Terms",
    "Privacy",
    "Legal Terms",
    "Legal",
    "Policy",
    "User Agreement",
    "User Policy",
    "Cookie Policy",
    "Cookie Consent",
    "Data Policy",
    "Data Privacy",
    "Privacy Statement",
    "Terms Statement",
    "Terms & Conditions",
    "Privacy Notice",
]

HGTV_MODAL_FOCUS_ORDER = [
    "heading: Legal Terms and Privacy",
    "link: Terms of Use",
    "link: Privacy Policy",
    "button: Accept terms and close the modal",
]

def _ui_hygiene() -> list[str]:
    return [
        "Ensure the page is fully loaded.",
        "Do not interact with page content behind the modal.",
    ]

def _modal_open_steps(url: str) -> list[str]:
    return [
        f"Go to url '{url}'.",
        *_ui_hygiene(),
        "Wait until the 'Legal Terms and Privacy' modal dialog appears.",
    ]

def _modal_accept_step(label: str) -> str:
    return f"Click the '{label}' button to accept terms and close the modal."

def _modal_link_step(link: str) -> str:
    return f"Click the link labeled '{link}' in the modal."

def _modal_link_keyboard_step(link: str) -> str:
    return f"Tab to the '{link}' link in the modal and press Enter."

def _modal_focus_order_steps() -> list[str]:
    return [
        "With the modal open, use Tab to cycle through all focusable elements.",
        "Verify the focus order is: heading, Terms of Use link, Privacy Policy link, Accept button.",
    ]

def _modal_negative_no_accept_step() -> str:
    return "Do not click the accept button. Attempt to interact with the main page content behind the modal."

def _modal_assert_modal_closed() -> str:
    return "Verify the modal dialog is no longer present and main page content is accessible."

def _modal_assert_modal_still_open() -> str:
    return "Verify the modal dialog remains present and main page content is still inaccessible."

def _modal_assert_link_navigated(link: str) -> str:
    return f"Verify that clicking the '{link}' link opens the correct legal page (URL or visible content)."

def _modal_assert_focus_order() -> str:
    return "Assert that focus order matches expected sequence and no elements are skipped."

def _modal_assert_multi_tab_link(link: str) -> str:
    return f"Right-click the '{link}' link and open in a new tab. Verify the correct legal page loads in the new tab."

def _modal_assert_repeat_accept() -> str:
    return "After accepting, reload the page and verify the modal does not reappear immediately."

def _modal_assert_multi_tab_modal() -> str:
    return "Open the site in two tabs. Accept the modal in one tab. Switch to the other tab and verify modal presence or absence."

def hgtv_accept_privacy_modal(_: dict) -> dict:
    url = random.choice(HGTV_MODAL_URLS)
    label = random.choice(HGTV_MODAL_ACCEPT_LABELS)
    steps = _modal_open_steps(url) + [
        _modal_accept_step(label),
        _modal_assert_modal_closed(),
    ]
    return {
        "task_type": "hgtv_accept_privacy_modal",
        "url": url,
        "accept_label": label,
        "steps": steps,
    }

def hgtv_open_terms_of_use(_: dict) -> dict:
    url = random.choice(HGTV_MODAL_URLS)
    link = "Terms of Use"
    steps = _modal_open_steps(url) + [
        _modal_link_step(link),
        _modal_assert_link_navigated(link),
    ]
    return {
        "task_type": "hgtv_open_terms_of_use",
        "url": url,
        "link": link,
        "steps": steps,
    }

def hgtv_open_privacy_policy(_: dict) -> dict:
    url = random.choice(HGTV_MODAL_URLS)
    link = "Privacy Policy"
    steps = _modal_open_steps(url) + [
        _modal_link_step(link),
        _modal_assert_link_navigated(link),
    ]
    return {
        "task_type": "hgtv_open_privacy_policy",
        "url": url,
        "link": link,
        "steps": steps,
    }

def hgtv_modal_negative_no_accept(_: dict) -> dict:
    url = random.choice(HGTV_MODAL_URLS)
    steps = _modal_open_steps(url) + [
        _modal_negative_no_accept_step(),
        _modal_assert_modal_still_open(),
    ]
    return {
        "task_type": "hgtv_modal_negative_no_accept",
        "url": url,
        "steps": steps,
    }

def hgtv_modal_link_navigation(_: dict) -> dict:
    url = random.choice(HGTV_MODAL_URLS)
    link = random.choice(HGTV_MODAL_LINK_VARIANTS)
    steps = _modal_open_steps(url) + [
        _modal_link_step(link),
        _modal_assert_link_navigated(link),
    ]
    return {
        "task_type": "hgtv_modal_link_navigation",
        "url": url,
        "link": link,
        "steps": steps,
    }

def hgtv_modal_repeat_accept(_: dict) -> dict:
    url = random.choice(HGTV_MODAL_URLS)
    label = random.choice(HGTV_MODAL_ACCEPT_LABELS)
    steps = _modal_open_steps(url) + [
        _modal_accept_step(label),
        _modal_assert_modal_closed(),
        "Reload the page.",
        _modal_assert_repeat_accept(),
    ]
    return {
        "task_type": "hgtv_modal_repeat_accept",
        "url": url,
        "accept_label": label,
        "steps": steps,
    }

def hgtv_modal_multi_tab_terms(_: dict) -> dict:
    url = random.choice(HGTV_MODAL_URLS)
    link = "Terms of Use"
    steps = _modal_open_steps(url) + [
        _modal_assert_multi_tab_link(link),
    ]
    return {
        "task_type": "hgtv_modal_multi_tab_terms",
        "url": url,
        "link": link,
        "steps": steps,
    }

def hgtv_modal_multi_tab_privacy(_: dict) -> dict:
    url = random.choice(HGTV_MODAL_URLS)
    link = "Privacy Policy"
    steps = _modal_open_steps(url) + [
        _modal_assert_multi_tab_link(link),
    ]
    return {
        "task_type": "hgtv_modal_multi_tab_privacy",
        "url": url,
        "link": link,
        "steps": steps,
    }

def hgtv_modal_link_keyboard(_: dict) -> dict:
    url = random.choice(HGTV_MODAL_URLS)
    link = random.choice(HGTV_MODAL_LINKS)
    steps = _modal_open_steps(url) + [
        _modal_link_keyboard_step(link),
        _modal_assert_link_navigated(link),
    ]
    return {
        "task_type": "hgtv_modal_link_keyboard",
        "url": url,
        "link": link,
        "steps": steps,
    }

def hgtv_modal_accessibility_focus(_: dict) -> dict:
    url = random.choice(HGTV_MODAL_URLS)
    steps = _modal_open_steps(url) + [
        *_modal_focus_order_steps(),
        _modal_assert_focus_order(),
    ]
    return {
        "task_type": "hgtv_modal_accessibility_focus",
        "url": url,
        "expected_focus_order": HGTV_MODAL_FOCUS_ORDER,
        "steps": steps,
    }

_TASK_GENERATORS: Dict[HGTV_TASK_TYPES, Callable[[dict], dict]] = {
    "hgtv_accept_privacy_modal": hgtv_accept_privacy_modal,
    "hgtv_open_terms_of_use": hgtv_open_terms_of_use,
    "hgtv_open_privacy_policy": hgtv_open_privacy_policy,
    "hgtv_modal_negative_no_accept": hgtv_modal_negative_no_accept,
    "hgtv_modal_link_navigation": hgtv_modal_link_navigation,
    "hgtv_modal_repeat_accept": hgtv_modal_repeat_accept,
    "hgtv_modal_multi_tab_terms": hgtv_modal_multi_tab_terms,
    "hgtv_modal_multi_tab_privacy": hgtv_modal_multi_tab_privacy,
    "hgtv_modal_link_keyboard": hgtv_modal_link_keyboard,
    "hgtv_modal_accessibility_focus": hgtv_modal_accessibility_focus,
}

def _instr(steps: list[str]) -> dict:
    return get_instruction("HGTV", steps).model_dump()

def generate_hgtv_task(task_type: HGTV_TASK_TYPES, payload: dict) -> dict:
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
    items = list(HGTV_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_hgtv_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)