import json
import random
import datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

WALMART_TASK_TYPES = Literal[
    "walmart_search_job_title",
    "walmart_filter_by_location",
    "walmart_browse_career_area",
    "walmart_explore_department",
    "walmart_apply_distribution_job",
    "walmart_expand_faq",
    "walmart_view_culture_story",
    "walmart_social_media_link",
    "walmart_footer_legal_link",
    "walmart_view_location_feature",
    "walmart_tab_navigation",
]

WALMART_SAMPLING_CONFIG: Dict[WALMART_TASK_TYPES, int] = {
    "walmart_search_job_title": 10,
    "walmart_filter_by_location": 10,
    "walmart_browse_career_area": 10,
    "walmart_explore_department": 10,
    "walmart_apply_distribution_job": 10,
    "walmart_expand_faq": 10,
    "walmart_view_culture_story": 10,
    "walmart_social_media_link": 10,
    "walmart_footer_legal_link": 10,
    "walmart_view_location_feature": 10,
    "walmart_tab_navigation": 10,
}

JOB_TITLES = [
    "Cashier", "Stocker", "Pharmacy Technician", "Truck Driver", "Store Manager", "Maintenance Associate", "Customer Service",
    "Greeter", "Fresh Food Associate", "Bakery Associate", "Deli Associate", "Produce Associate", "Meat Cutter", "Optician",
    "Auto Care Center Technician", "Asset Protection", "HR Coordinator", "E-Commerce Associate", "Order Filler", "Warehouse Worker",
    "Forklift Operator", "Team Lead", "Merchandiser", "Sales Associate", "Personal Shopper", "Receiving Associate"
]

LOCATIONS = [
    "Bentonville, AR", "Dallas, TX", "Atlanta, GA", "Chicago, IL", "Los Angeles, CA", "Houston, TX", "Miami, FL", "Phoenix, AZ",
    "Orlando, FL", "San Francisco, CA", "Seattle, WA", "Denver, CO", "Minneapolis, MN", "Charlotte, NC", "Washington, DC",
    "New York, NY", "Boston, MA", "Las Vegas, NV", "San Diego, CA", "Salt Lake City, UT", "Indianapolis, IN", "Columbus, OH",
    "Kansas City, MO", "Nashville, TN", "Portland, OR"
]

CAREER_AREAS = [
    "Stores & Clubs", "Corporate", "Healthcare", "Technology", "Distribution, Fulfillment, & Drivers", "Asset Protection",
    "Finance & Accounting", "Human Resources", "Legal", "Marketing", "Merchandising", "Real Estate", "Supply Chain",
    "E-Commerce", "Customer Service", "Pharmacy", "Optical", "Auto Care", "Maintenance", "Bakery", "Deli", "Produce",
    "Meat", "Fresh Food", "Order Fulfillment"
]

DEPARTMENTS = [
    "Distribution and Fulfillment Centers", "Drivers & Transportation", "Fleet Maintenance", "Flex Associate", "Manufacturing",
    "Order Fulfillment", "Logistics", "Inventory Management", "Shipping", "Receiving", "Returns", "Quality Control",
    "Packaging", "Material Handling", "Warehouse Operations", "Supply Chain Analytics", "Dispatch", "Route Planning",
    "Safety Compliance", "Equipment Maintenance", "Scheduling", "Load Planning"
]

FAQ_QUESTIONS = [
    "How long does it take to complete an application?",
    "What is the status of my application?",
    "Can I apply for multiple jobs?",
    "How do I reset my password?",
    "What documents do I need to apply?",
    "How do I update my profile?",
    "What is the interview process?",
    "How do I withdraw my application?",
    "Can I apply without an account?",
    "How do I contact support?",
    "What are the age requirements?",
    "Are there part-time jobs?",
    "How do I check my background check status?",
    "How do I get job alerts?",
    "How do I upload my resume?",
    "What is the pay rate?",
    "How do I schedule an interview?",
    "What is the dress code?",
    "How do I get benefits information?",
    "How do I find jobs near me?",
    "How do I apply for remote jobs?",
    "How do I refer a friend?",
    "How do I access the FAQ page?"
]

CULTURE_STORIES = [
    "Culture of Success", "Smart Benefits", "Investing in American Jobs", "Culture of Belonging", "Education Benefit",
    "Walmart Human Resources Culture of Belonging", "Our story", "American renewal", "Family business"
]

SOCIAL_MEDIA = [
    "Facebook", "Twitter", "LinkedIn", "Instagram", "Glassdoor", "YouTube", "Pinterest", "TikTok", "Snapchat", "Reddit",
    "WhatsApp", "Telegram", "WeChat", "Line", "Viber", "Tumblr", "Flickr", "Medium", "Quora", "Discord"
]

FOOTER_LEGAL = [
    "FAQ", "Sitemap", "Corporate", "Terms & Conditions", "Privacy Policy", "Notice at Collection", "applicant rights under Federal Employment Laws",
    "Accessibility", "EEO Statement", "E-Verify", "California Privacy Rights", "Do Not Sell My Info", "Cookie Policy",
    "Security", "Contact Us", "Legal Notices", "Supplier Information", "Investor Relations", "Press Center", "Careers"
]

LOCATION_FEATURES = [
    {"name": "Northwest Arkansas", "url": "https://careers.walmart.com/", "feature": "biking and hiking trails"},
    {"name": "Silicon Valley", "url": "https://careers.walmart.com/", "feature": "technological innovation"},
    {"name": "D.C. Metro", "url": "https://careers.walmart.com/", "feature": "national landmarks"},
    {"name": "Dallas", "url": "https://careers.walmart.com/", "feature": "urban culture"},
    {"name": "Atlanta", "url": "https://careers.walmart.com/", "feature": "southern hospitality"},
    {"name": "Chicago", "url": "https://careers.walmart.com/", "feature": "architecture"},
    {"name": "Los Angeles", "url": "https://careers.walmart.com/", "feature": "entertainment industry"},
    {"name": "Houston", "url": "https://careers.walmart.com/", "feature": "space center"},
    {"name": "Miami", "url": "https://careers.walmart.com/", "feature": "beaches"},
    {"name": "Phoenix", "url": "https://careers.walmart.com/", "feature": "desert landscapes"},
    {"name": "Orlando", "url": "https://careers.walmart.com/", "feature": "theme parks"},
    {"name": "San Francisco", "url": "https://careers.walmart.com/", "feature": "Golden Gate Bridge"},
    {"name": "Seattle", "url": "https://careers.walmart.com/", "feature": "tech hub"},
    {"name": "Denver", "url": "https://careers.walmart.com/", "feature": "mountain access"},
    {"name": "Minneapolis", "url": "https://careers.walmart.com/", "feature": "lakes"},
    {"name": "Charlotte", "url": "https://careers.walmart.com/", "feature": "banking center"},
    {"name": "New York", "url": "https://careers.walmart.com/", "feature": "city life"},
    {"name": "Boston", "url": "https://careers.walmart.com/", "feature": "history"},
    {"name": "Las Vegas", "url": "https://careers.walmart.com/", "feature": "entertainment"},
    {"name": "San Diego", "url": "https://careers.walmart.com/", "feature": "beaches"},
    {"name": "Salt Lake City", "url": "https://careers.walmart.com/", "feature": "skiing"},
    {"name": "Indianapolis", "url": "https://careers.walmart.com/", "feature": "auto racing"}
]

TABS = [
    "Stores & Clubs", "Corporate", "Healthcare", "Technology", "Distribution, Fulfillment, & Drivers",
    "Pharmacy", "Optical", "Auto Care", "Maintenance", "Bakery", "Deli", "Produce", "Meat", "Fresh Food",
    "Order Fulfillment", "Asset Protection", "Finance & Accounting", "Human Resources", "Legal", "Marketing", "Supply Chain"
]

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups or banners if present.",
        "Do not submit personal information or complete any purchases.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Walmart Careers", steps).model_dump()

def walmart_search_job_title(_: dict) -> dict:
    job_title = random.choice(JOB_TITLES)
    steps = [
        "Go to url 'https://careers.walmart.com/'.",
        *_ui_hygiene(),
        "Locate the 'Search input' textbox.",
        f"Type '{job_title}' into the search box.",
        "Click the 'Search' button.",
        f"Verify that job results are shown for '{job_title}'.",
        "Check that at least one job listing contains the searched title.",
        "If no results are found, confirm a 'no results' or similar message is displayed."
    ]
    return {
        "task_type": "walmart_search_job_title",
        "job_title": job_title,
        "steps": steps,
        "assertion": f"Job results for '{job_title}' are displayed or a 'no results' message appears."
    }

def walmart_filter_by_location(_: dict) -> dict:
    location = random.choice(LOCATIONS)
    steps = [
        "Go to url 'https://careers.walmart.com/'.",
        *_ui_hygiene(),
        "Locate the 'Location' textbox.",
        f"Type '{location}' into the location box.",
        "Click the 'Search' button.",
        f"Verify that job results are filtered for '{location}'.",
        "Check that the top job listings reference the selected location.",
        "If no results are found, confirm a 'no jobs found' or similar message is displayed."
    ]
    return {
        "task_type": "walmart_filter_by_location",
        "location": location,
        "steps": steps,
        "assertion": f"Job results for '{location}' are displayed or a 'no jobs found' message appears."
    }

def walmart_browse_career_area(_: dict) -> dict:
    area = random.choice(CAREER_AREAS)
    steps = [
        "Go to url 'https://careers.walmart.com/'.",
        *_ui_hygiene(),
        "Locate the 'All Career Areas' link or button.",
        "Click 'All Career Areas'.",
        f"On the career areas page, select '{area}'.",
        f"Verify that the page for '{area}' loads and displays relevant job categories.",
        "Check that at least one job or description is visible for the selected area."
    ]
    return {
        "task_type": "walmart_browse_career_area",
        "career_area": area,
        "steps": steps,
        "assertion": f"Career area page for '{area}' loads with relevant jobs or descriptions."
    }

def walmart_explore_department(_: dict) -> dict:
    department = random.choice(DEPARTMENTS)
    steps = [
        "Go to url 'https://careers.walmart.com/distribution-fulfillment-drivers'.",
        *_ui_hygiene(),
        f"Find and click the '{department}' department link.",
        f"Verify that jobs or information for '{department}' are displayed.",
        "Check that at least one job or description is visible for the selected department."
    ]
    return {
        "task_type": "walmart_explore_department",
        "department": department,
        "steps": steps,
        "assertion": f"Department page for '{department}' loads with relevant jobs or descriptions."
    }

def walmart_apply_distribution_job(_: dict) -> dict:
    job_types = [
        "Drivers", "Distribution Centers", "Fleet Maintenance", "Flex Associate", "Manufacturing"
    ]
    job_type = random.choice(job_types)
    steps = [
        "Go to url 'https://careers.walmart.com/distribution-fulfillment-drivers'.",
        *_ui_hygiene(),
        f"Locate the '{job_type}' section.",
        f"Click the 'Apply' button under '{job_type}'.",
        "Verify that the application page for the selected job type loads.",
        "Check that the application form or job details for the selected job type are visible.",
        "Do not submit the application."
    ]
    return {
        "task_type": "walmart_apply_distribution_job",
        "job_type": job_type,
        "steps": steps,
        "assertion": f"Application page for '{job_type}' is loaded and form is visible."
    }

def walmart_expand_faq(_: dict) -> dict:
    faq = random.choice(FAQ_QUESTIONS)
    steps = [
        "Go to url 'https://careers.walmart.com/'.",
        *_ui_hygiene(),
        "Scroll to the FAQ section or locate the FAQ link.",
        "Expand the FAQ section if collapsed.",
        f"Click the FAQ question: '{faq}'.",
        "Verify that the answer to the selected FAQ is displayed.",
        "Collapse the FAQ and confirm the answer is hidden."
    ]
    return {
        "task_type": "walmart_expand_faq",
        "faq_question": faq,
        "steps": steps,
        "assertion": f"Answer for FAQ '{faq}' is shown when expanded and hidden when collapsed."
    }

def walmart_view_culture_story(_: dict) -> dict:
    story = random.choice(CULTURE_STORIES)
    steps = [
        "Go to url 'https://careers.walmart.com/'.",
        *_ui_hygiene(),
        f"Scroll to the section for '{story}' or locate its 'LEARN MORE' link.",
        f"Click the 'LEARN MORE' link for '{story}'.",
        f"Verify that a new page or modal opens with information about '{story}'.",
        "Check that at least one paragraph or video about the story is visible."
    ]
    return {
        "task_type": "walmart_view_culture_story",
        "culture_story": story,
        "steps": steps,
        "assertion": f"'{story}' story page or modal opens and displays relevant content."
    }

def walmart_social_media_link(_: dict) -> dict:
    sm = random.choice(SOCIAL_MEDIA)
    steps = [
        "Go to url 'https://careers.walmart.com/'.",
        *_ui_hygiene(),
        "Scroll to the footer or social media section.",
        f"Click the '{sm}' social media link (opens in new window).",
        f"Verify that a new tab or window opens to the official Walmart {sm} page.",
        "Check that the page title or branding matches Walmart's official account."
    ]
    return {
        "task_type": "walmart_social_media_link",
        "social_media": sm,
        "steps": steps,
        "assertion": f"New tab/window opens to Walmart's official {sm} page."
    }

def walmart_footer_legal_link(_: dict) -> dict:
    link = random.choice(FOOTER_LEGAL)
    steps = [
        "Go to url 'https://careers.walmart.com/'.",
        *_ui_hygiene(),
        "Scroll to the footer section.",
        f"Click the '{link}' link.",
        f"Verify that the corresponding legal or informational page for '{link}' loads.",
        "Check that the page contains expected legal or informational content."
    ]
    return {
        "task_type": "walmart_footer_legal_link",
        "footer_link": link,
        "steps": steps,
        "assertion": f"Legal/informational page for '{link}' loads with expected content."
    }

def walmart_view_location_feature(_: dict) -> dict:
    loc = random.choice(LOCATION_FEATURES)
    steps = [
        "Go to url 'https://careers.walmart.com/'.",
        *_ui_hygiene(),
        f"Scroll to the '{loc['name']}' featured location section.",
        "Read the short description or feature text.",
        "Click the 'Find out more' link for this location.",
        "Verify that a new page or modal opens with more information about the location.",
        f"Check that the location's key feature ('{loc['feature']}') is mentioned."
    ]
    return {
        "task_type": "walmart_view_location_feature",
        "location": loc['name'],
        "feature": loc['feature'],
        "steps": steps,
        "assertion": f"'{loc['name']}' feature page/modal opens and mentions '{loc['feature']}'."
    }

def walmart_tab_navigation(_: dict) -> dict:
    tab = random.choice(TABS)
    steps = [
        "Go to url 'https://careers.walmart.com/'.",
        *_ui_hygiene(),
        f"Locate and click the '{tab}' tab.",
        f"Verify that the page or section for '{tab}' loads.",
        "Check that relevant job categories or descriptions for the selected tab are visible.",
        "Navigate back to the main page and confirm the main content is restored."
    ]
    return {
        "task_type": "walmart_tab_navigation",
        "tab": tab,
        "steps": steps,
        "assertion": f"Tab '{tab}' loads correct content and navigation back restores main page."
    }

_TASK_GENERATORS: Dict[WALMART_TASK_TYPES, Callable[[dict], dict]] = {
    "walmart_search_job_title": walmart_search_job_title,
    "walmart_filter_by_location": walmart_filter_by_location,
    "walmart_browse_career_area": walmart_browse_career_area,
    "walmart_explore_department": walmart_explore_department,
    "walmart_apply_distribution_job": walmart_apply_distribution_job,
    "walmart_expand_faq": walmart_expand_faq,
    "walmart_view_culture_story": walmart_view_culture_story,
    "walmart_social_media_link": walmart_social_media_link,
    "walmart_footer_legal_link": walmart_footer_legal_link,
    "walmart_view_location_feature": walmart_view_location_feature,
    "walmart_tab_navigation": walmart_tab_navigation,
}

def generate_walmart_task(task_type: WALMART_TASK_TYPES, payload: dict) -> dict:
    task = _TASK_GENERATORS[task_type](payload or {})
    task["instruction"] = _instr(task["steps"])
    return task

def main(filepath: str, payloads_json: str = "", num_workers: int = 12, timeout: int = 60, seed: int = 42, indent: int = 2):
    payloads = []
    if payloads_json:
        with open(payloads_json) as f:
            payloads = json.load(f)
    if not isinstance(payloads, list):
        payloads = []
    random.seed(seed)
    futures, out = [], []
    items = list(WALMART_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_walmart_task, ttype, p))
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