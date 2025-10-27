import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

ADP_TASK_TYPES = Literal[
    "adp_login_error",
    "adp_privacy_link",
    "adp_legal_link",
    "adp_reload_main",
    "adp_error_message_presence",
    "adp_error_message_language",
    "adp_contact_admin_text",
    "adp_copyright_years",
    "adp_link_navigation",
    "adp_refresh_browser",
    "adp_accessibility_texts",
    "adp_error_banner",
    "adp_privacy_legal_links",
]

ADP_SAMPLING_CONFIG: Dict[ADP_TASK_TYPES, int] = {
    "adp_login_error": 10,
    "adp_privacy_link": 10,
    "adp_legal_link": 10,
    "adp_reload_main": 10,
    "adp_error_message_presence": 10,
    "adp_error_message_language": 10,
    "adp_contact_admin_text": 10,
    "adp_copyright_years": 10,
    "adp_link_navigation": 10,
    "adp_refresh_browser": 10,
    "adp_accessibility_texts": 10,
    "adp_error_banner": 10,
    "adp_privacy_legal_links": 10,
}

# For variable selectors
BROWSERS = [
    "Chrome", "Firefox", "Edge", "Safari", "Opera", "Brave", "Vivaldi", "Chromium", "IE11", "Samsung Internet",
    "UC Browser", "Maxthon", "Puffin", "Dolphin", "Yandex", "Epic", "Comodo Dragon", "SRWare Iron", "Torch", "Sleipnir"
]
LANGUAGES = [
    "en", "es", "fr", "de", "it", "pt", "zh", "ja", "ko", "ru", "ar", "tr", "pl", "nl", "sv", "fi", "da", "no", "cs", "el"
]
YEARS = [str(y) for y in range(2000, 2026)]
ERROR_VARIANTS = [
    "An error occurred while processing this request.",
    "Close your browser and try again.",
    "If you continue to experience problems,",
    "contact your system administrator.",
]
PRIVACY_LINKS = [
    "Privacy", "Legal"
]
LINK_DESTINATIONS = [
    "Privacy", "Legal"
]
REFRESH_METHODS = [
    "browser refresh button", "F5 key", "Ctrl+R", "Cmd+R", "right-click and Reload", "address bar Enter",
    "browser menu Reload", "Shift+F5", "Ctrl+Shift+R", "Cmd+Shift+R", "reopen tab", "close and reopen browser",
    "open in new tab", "clear cache and reload", "incognito window", "private window", "browser restart",
    "reload from history", "reload via developer tools", "reload via bookmarks", "reload via shortcut"
]
ACCESSIBILITY_TEXTS = [
    "An error occurred while processing this request.",
    "Close your browser and try again.",
    "If you continue to experience problems,",
    "contact your system administrator.",
    "Privacy",
    "Legal",
    "Copyright © 2000 - ",
    "2025 ADP, Inc. All rights reserved."
]
ERROR_BANNER_VARIANTS = [
    "An error occurred while processing this request.",
    "Close your browser and try again.",
    "If you continue to experience problems,",
    "contact your system administrator."
]

def _ui_hygiene() -> list[str]:
    return [
        "Ensure no popups or overlays are blocking the main content.",
        "Do not enter any personal or sensitive information.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("ADP", steps).model_dump()

def adp_login_error(_: dict) -> dict:
    browser = random.choice(BROWSERS)
    steps = [
        f"Go to url 'https://online.adp.com' in a {browser} browser.",
        *_ui_hygiene(),
        "Wait for the page to load.",
        "Verify that an error message is visible on the page.",
        "Assert that the message includes the text: 'An error occurred while processing this request.'",
        "Do not attempt to sign in or enter credentials.",
    ]
    return {
        "task_type": "adp_login_error",
        "browser": browser,
        "steps": steps,
        "assertion": "Error message is present and visible."
    }

def adp_privacy_link(_: dict) -> dict:
    steps = [
        "Go to url 'https://online.adp.com'.",
        *_ui_hygiene(),
        "Scroll to the bottom of the page.",
        "Locate the link labeled 'Privacy'.",
        "Click the 'Privacy' link.",
        "Verify that a new page or tab opens, or the URL changes.",
        "Assert the new page contains privacy-related information.",
    ]
    return {
        "task_type": "adp_privacy_link",
        "steps": steps,
        "assertion": "Privacy link is present, clickable, and leads to privacy information."
    }

def adp_legal_link(_: dict) -> dict:
    steps = [
        "Go to url 'https://online.adp.com'.",
        *_ui_hygiene(),
        "Scroll to the bottom of the page.",
        "Locate the link labeled 'Legal'.",
        "Click the 'Legal' link.",
        "Verify that a new page or tab opens, or the URL changes.",
        "Assert the new page contains legal or terms of use information.",
    ]
    return {
        "task_type": "adp_legal_link",
        "steps": steps,
        "assertion": "Legal link is present, clickable, and leads to legal information."
    }

def adp_reload_main(_: dict) -> dict:
    method = random.choice(REFRESH_METHODS)
    steps = [
        "Go to url 'https://online.adp.com'.",
        *_ui_hygiene(),
        f"Reload the page using the {method}.",
        "Wait for the page to reload.",
        "Verify that the error message is still present after reload.",
        "Assert the error message text matches the original.",
    ]
    return {
        "task_type": "adp_reload_main",
        "reload_method": method,
        "steps": steps,
        "assertion": "Error message persists after reload."
    }

def adp_error_message_presence(_: dict) -> dict:
    error_text = random.choice(ERROR_VARIANTS)
    steps = [
        "Go to url 'https://online.adp.com'.",
        *_ui_hygiene(),
        f"Check that the following error message is present: '{error_text}'",
        "Assert the message is visible and not hidden by overlays.",
    ]
    return {
        "task_type": "adp_error_message_presence",
        "error_text": error_text,
        "steps": steps,
        "assertion": f"Error message '{error_text}' is visible."
    }

def adp_error_message_language(_: dict) -> dict:
    lang = random.choice(LANGUAGES)
    steps = [
        f"Go to url 'https://online.adp.com' with browser language set to '{lang}'.",
        *_ui_hygiene(),
        "Wait for the page to load.",
        "Check if the error message appears in the selected language.",
        "If not, assert the message is in English.",
    ]
    return {
        "task_type": "adp_error_message_language",
        "language": lang,
        "steps": steps,
        "assertion": "Error message appears in selected language or defaults to English."
    }

def adp_contact_admin_text(_: dict) -> dict:
    steps = [
        "Go to url 'https://online.adp.com'.",
        *_ui_hygiene(),
        "Look for the text: 'contact your system administrator.'",
        "Assert that the text is present and visible.",
        "Verify that no clickable link is present on this text.",
    ]
    return {
        "task_type": "adp_contact_admin_text",
        "steps": steps,
        "assertion": "Text 'contact your system administrator.' is present and not a link."
    }

def adp_copyright_years(_: dict) -> dict:
    year = random.choice(YEARS)
    steps = [
        "Go to url 'https://online.adp.com'.",
        *_ui_hygiene(),
        "Scroll to the bottom of the page.",
        "Locate the copyright text.",
        f"Assert that the copyright includes the year '{year}' or a range including '{year}'.",
        "Verify the text includes 'ADP, Inc. All rights reserved.'",
    ]
    return {
        "task_type": "adp_copyright_years",
        "year": year,
        "steps": steps,
        "assertion": f"Copyright includes year '{year}' and 'ADP, Inc. All rights reserved.'"
    }

def adp_link_navigation(_: dict) -> dict:
    link = random.choice(LINK_DESTINATIONS)
    steps = [
        "Go to url 'https://online.adp.com'.",
        *_ui_hygiene(),
        f"Find and click the '{link}' link at the bottom of the page.",
        "Wait for navigation.",
        f"Assert that the new page or tab contains the word '{link.lower()}' in the title or main heading.",
    ]
    return {
        "task_type": "adp_link_navigation",
        "link": link,
        "steps": steps,
        "assertion": f"Navigation to '{link}' page is successful."
    }

def adp_refresh_browser(_: dict) -> dict:
    browser = random.choice(BROWSERS)
    steps = [
        f"Open 'https://online.adp.com' in {browser}.",
        *_ui_hygiene(),
        "Wait for the page to load.",
        "Refresh the page using the browser's built-in refresh.",
        "Assert that the error message is still present after refresh.",
    ]
    return {
        "task_type": "adp_refresh_browser",
        "browser": browser,
        "steps": steps,
        "assertion": "Error message persists after browser refresh."
    }

def adp_accessibility_texts(_: dict) -> dict:
    text = random.choice(ACCESSIBILITY_TEXTS)
    steps = [
        "Go to url 'https://online.adp.com'.",
        *_ui_hygiene(),
        f"Using accessibility tools or screen reader, locate the text: '{text}'.",
        "Assert that the text is exposed to assistive technologies.",
    ]
    return {
        "task_type": "adp_accessibility_texts",
        "accessibility_text": text,
        "steps": steps,
        "assertion": f"Text '{text}' is accessible to screen readers."
    }

def adp_error_banner(_: dict) -> dict:
    banner = random.choice(ERROR_BANNER_VARIANTS)
    steps = [
        "Go to url 'https://online.adp.com'.",
        *_ui_hygiene(),
        f"Check for a visible error banner containing: '{banner}'.",
        "Assert the banner is styled as an error (e.g., red or prominent).",
        "Verify it is not dismissible by the user.",
    ]
    return {
        "task_type": "adp_error_banner",
        "banner_text": banner,
        "steps": steps,
        "assertion": f"Error banner with '{banner}' is visible and not dismissible."
    }

def adp_privacy_legal_links(_: dict) -> dict:
    link = random.choice(PRIVACY_LINKS)
    steps = [
        "Go to url 'https://online.adp.com'.",
        *_ui_hygiene(),
        f"Locate both 'Privacy' and 'Legal' links at the bottom of the page.",
        f"Click the '{link}' link.",
        f"Assert that the new page or tab contains relevant {link.lower()} information.",
        "Go back to the main page and repeat for the other link.",
    ]
    return {
        "task_type": "adp_privacy_legal_links",
        "link": link,
        "steps": steps,
        "assertion": f"Both 'Privacy' and 'Legal' links are present and lead to correct content."
    }

_TASK_GENERATORS: Dict[ADP_TASK_TYPES, Callable[[dict], dict]] = {
    "adp_login_error": adp_login_error,
    "adp_privacy_link": adp_privacy_link,
    "adp_legal_link": adp_legal_link,
    "adp_reload_main": adp_reload_main,
    "adp_error_message_presence": adp_error_message_presence,
    "adp_error_message_language": adp_error_message_language,
    "adp_contact_admin_text": adp_contact_admin_text,
    "adp_copyright_years": adp_copyright_years,
    "adp_link_navigation": adp_link_navigation,
    "adp_refresh_browser": adp_refresh_browser,
    "adp_accessibility_texts": adp_accessibility_texts,
    "adp_error_banner": adp_error_banner,
    "adp_privacy_legal_links": adp_privacy_legal_links,
}

def generate_adp_task(task_type: ADP_TASK_TYPES, payload: dict) -> dict:
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
    items = list(ADP_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_adp_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)