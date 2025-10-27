import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

AMZN_TASK_TYPES = Literal[
    "amzn_keyword_search",
    "amzn_location_search",
    "amzn_job_category_filter",
    "amzn_team_filter",
    "amzn_job_type_filter",
    "amzn_apply_now_button",
    "amzn_save_job_flow",
    "amzn_job_description_assert",
    "amzn_language_selector",
    "amzn_help_center_topic"
]

AMZN_SAMPLING_CONFIG: Dict[AMZN_TASK_TYPES, int] = {
    "amzn_keyword_search": 10,
    "amzn_location_search": 10,
    "amzn_job_category_filter": 10,
    "amzn_team_filter": 10,
    "amzn_job_type_filter": 10,
    "amzn_apply_now_button": 10,
    "amzn_save_job_flow": 10,
    "amzn_job_description_assert": 10,
    "amzn_language_selector": 10,
    "amzn_help_center_topic": 10,
}

AMZN_KEYWORDS = [
    "Software Engineer", "Data Scientist", "Operations Manager", "UX Designer", "Product Manager",
    "Business Analyst", "Support Engineer", "Marketing", "Finance", "Legal", "HR", "Logistics",
    "Cloud Architect", "Machine Learning", "Quality Assurance", "Security Engineer", "Content Writer",
    "Customer Service", "Intern", "Research", "Sales", "Recruiter", "Supply Chain", "Warehouse", "Fulfillment"
]

AMZN_LOCATIONS = [
    "Seattle, WA, USA", "New York, NY, USA", "San Francisco, CA, USA", "Austin, TX, USA", "Boston, MA, USA",
    "Chicago, IL, USA", "Dallas, TX, USA", "Los Angeles, CA, USA", "Arlington, VA, USA", "Nashville, TN, USA",
    "Phoenix, AZ, USA", "Denver, CO, USA", "Atlanta, GA, USA", "London, England, GBR", "Berlin, Germany",
    "Luxembourg, Luxembourg", "Toronto, ON, Canada", "Vancouver, BC, Canada", "Madrid, Spain", "Paris, France",
    "Hyderabad, India", "Bangalore, India", "Cape Town, South Africa", "Tokyo, Japan", "Singapore, Singapore"
]

AMZN_JOB_CATEGORIES = [
    "Software Development", "Operations, IT, & Support Engineering", "Solutions Architect", "Project/Program/Product Management--Technical",
    "Human Resources", "Finance and Global Business Services", "Sales, Advertising, & Account Management", "Business Intelligence",
    "Fulfillment & Operations Management", "Data Science", "Design", "Legal", "Machine Learning Science", "Medical, Health, & Safety",
    "Public Policy", "Research Science", "Supply Chain/Transportation Management", "Writing, Editing, & Content Management",
    "Administrative Support", "Customer Service", "Facilities, Maintenance, & Real Estate", "Marketing", "Security & Loss Prevention",
    "System, Quality, & Security Engineering", "Training & Development"
]

AMZN_TEAMS = [
    "Amazon Web Services", "Prime Video", "Alexa", "Amazon Devices", "Amazon Fresh", "Amazon Studios", "Kindle", "Amazon Advertising",
    "Amazon Music", "Amazon Robotics", "Amazon Go", "Amazon Logistics", "Amazon Pharmacy", "Amazon Fashion", "Amazon Prime Air",
    "Amazon Game Studios", "Amazon Marketplace", "Amazon Transportation Services", "Amazon Business", "Amazon Pay",
    "Amazon Books", "Amazon Photos", "Amazon Appstore", "Amazon Publishing", "Amazon Care"
]

AMZN_JOB_TYPES = [
    "Full Time", "Part Time", "Internship", "Seasonal", "Contract", "Temporary", "Graduate", "Entry Level", "Mid Level", "Senior Level",
    "Remote", "Onsite", "Hybrid", "Apprenticeship", "Hourly", "Permanent", "Fixed Term", "Rotational", "Night Shift", "Day Shift",
    "Weekend", "Evening", "Flexible", "Management", "Individual Contributor"
]

AMZN_LANGUAGES = [
    "English", "Deutsch", "Français", "Español", "Italiano", "Português", "日本語", "한국어", "中文(简体)", "中文(繁體)",
    "Nederlands", "Polski", "Türkçe", "Svenska", "Norsk", "Suomi", "Dansk", "Русский", "Čeština", "Magyar",
    "Ελληνικά", "Română", "Українська", "עברית", "العربية"
]

AMZN_HELP_TOPICS = [
    "Application Process", "Interview Preparation", "Account Access Issues", "Job Alerts", "Resume Tips", "Diversity & Inclusion",
    "Internships", "Military Recruiting", "Disability Accommodations", "Relocation", "COVID-19 Updates", "Benefits Overview",
    "Amazon Culture", "Remote Work", "Hiring Events", "Student Programs", "Technical Support", "Background Checks",
    "Visa Sponsorship", "Fraudulent Offers", "Contact Us", "Job Notifications", "Password Reset", "Assessment Tests", "FAQ"
]

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups, cookie banners, or overlays if present.",
        "Do not submit any personal information or apply for jobs unless instructed.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Amazon Jobs", steps).model_dump()

def amzn_keyword_search(_: dict) -> dict:
    keyword = random.choice(AMZN_KEYWORDS)
    steps = [
        "Go to url 'https://www.amazon.jobs/'.",
        *_ui_hygiene(),
        "Locate the main job search input field (labeled 'Search for jobs' or similar).",
        f"Type '{keyword}' into the search field.",
        "Press Enter or click the search button.",
        "Wait for search results to load.",
        f"Assert that at least one job result contains the keyword '{keyword}' in the title or description.",
        "If no results, assert that a 'No jobs found' or similar message is displayed.",
    ]
    return {"task_type": "amzn_keyword_search", "keyword": keyword, "steps": steps}

def amzn_location_search(_: dict) -> dict:
    location = random.choice(AMZN_LOCATIONS)
    steps = [
        "Go to url 'https://www.amazon.jobs/'.",
        *_ui_hygiene(),
        "Locate the location search input field (labeled 'Location' or similar).",
        f"Type '{location}' into the location field.",
        "Select the suggested location from the dropdown if it appears.",
        "Press Enter or click the search button.",
        "Wait for search results to load.",
        f"Assert that all job results are located in or near '{location}' (city or country match).",
        "If no results, assert that a 'No jobs found' or similar message is displayed.",
    ]
    return {"task_type": "amzn_location_search", "location": location, "steps": steps}

def amzn_job_category_filter(_: dict) -> dict:
    category = random.choice(AMZN_JOB_CATEGORIES)
    steps = [
        "Go to url 'https://www.amazon.jobs/'.",
        *_ui_hygiene(),
        "Locate and open the 'Job Categories' filter or dropdown.",
        f"Select the category '{category}'.",
        "Apply the filter.",
        "Wait for filtered results to load.",
        f"Assert that all visible job results are within the '{category}' category.",
        "If no results, assert that a 'No jobs found' or similar message is displayed.",
    ]
    return {"task_type": "amzn_job_category_filter", "category": category, "steps": steps}

def amzn_team_filter(_: dict) -> dict:
    team = random.choice(AMZN_TEAMS)
    steps = [
        "Go to url 'https://www.amazon.jobs/'.",
        *_ui_hygiene(),
        "Locate and open the 'Team' or 'Business Unit' filter.",
        f"Select the team '{team}'.",
        "Apply the filter.",
        "Wait for filtered results to load.",
        f"Assert that all visible job results are for the '{team}' team or mention it in the description.",
        "If no results, assert that a 'No jobs found' or similar message is displayed.",
    ]
    return {"task_type": "amzn_team_filter", "team": team, "steps": steps}

def amzn_job_type_filter(_: dict) -> dict:
    job_type = random.choice(AMZN_JOB_TYPES)
    steps = [
        "Go to url 'https://www.amazon.jobs/'.",
        *_ui_hygiene(),
        "Locate and open the 'Job Type' or 'Employment Type' filter.",
        f"Select the job type '{job_type}'.",
        "Apply the filter.",
        "Wait for filtered results to load.",
        f"Assert that all visible job results are labeled as '{job_type}' or match the type.",
        "If no results, assert that a 'No jobs found' or similar message is displayed.",
    ]
    return {"task_type": "amzn_job_type_filter", "job_type": job_type, "steps": steps}

def amzn_apply_now_button(_: dict) -> dict:
    keyword = random.choice(AMZN_KEYWORDS)
    steps = [
        "Go to url 'https://www.amazon.jobs/'.",
        *_ui_hygiene(),
        "Locate the main job search input field.",
        f"Type '{keyword}' and press Enter.",
        "Wait for search results to load.",
        "Click on the first job result to open its detail page.",
        "Locate the 'Apply Now' button.",
        "Assert that the 'Apply Now' button is visible and enabled.",
        "Do not proceed with the application.",
    ]
    return {"task_type": "amzn_apply_now_button", "keyword": keyword, "steps": steps}

def amzn_save_job_flow(_: dict) -> dict:
    keyword = random.choice(AMZN_KEYWORDS)
    steps = [
        "Go to url 'https://www.amazon.jobs/'.",
        *_ui_hygiene(),
        "Locate the main job search input field.",
        f"Type '{keyword}' and press Enter.",
        "Wait for search results to load.",
        "Click on the first job result to open its detail page.",
        "Locate the 'Save Job' or bookmark button/icon.",
        "Click the 'Save Job' button.",
        "If prompted to sign in, assert that a sign-in modal or page appears.",
        "If not prompted, assert that the job is marked as saved (icon changes or confirmation banner appears).",
    ]
    return {"task_type": "amzn_save_job_flow", "keyword": keyword, "steps": steps}

def amzn_job_description_assert(_: dict) -> dict:
    keyword = random.choice(AMZN_KEYWORDS)
    steps = [
        "Go to url 'https://www.amazon.jobs/'.",
        *_ui_hygiene(),
        "Locate the main job search input field.",
        f"Type '{keyword}' and press Enter.",
        "Wait for search results to load.",
        "Click on the first job result to open its detail page.",
        "Assert that the job description section is visible and contains at least 100 characters.",
        "Assert that the job title matches or contains the keyword.",
        "Assert that there is a 'Basic Qualifications' or 'Preferred Qualifications' section.",
    ]
    return {"task_type": "amzn_job_description_assert", "keyword": keyword, "steps": steps}

def amzn_language_selector(_: dict) -> dict:
    language = random.choice(AMZN_LANGUAGES)
    steps = [
        "Go to url 'https://www.amazon.jobs/'.",
        *_ui_hygiene(),
        "Locate the language selector dropdown or menu (often at the top or bottom of the page).",
        f"Select '{language}' from the language options.",
        "Wait for the page to reload or update.",
        f"Assert that the page content is displayed in '{language}' (check main headings or navigation).",
        "If the language is not available, assert that an error or fallback occurs.",
    ]
    return {"task_type": "amzn_language_selector", "language": language, "steps": steps}

def amzn_help_center_topic(_: dict) -> dict:
    topic = random.choice(AMZN_HELP_TOPICS)
    steps = [
        "Go to url 'https://www.amazon.jobs/en/help'.",
        *_ui_hygiene(),
        f"Locate and click on the help topic '{topic}' (or its closest match).",
        "Wait for the topic content to load.",
        f"Assert that the help page or section for '{topic}' is displayed and contains at least 2 paragraphs.",
        "If the topic is not found, assert that a 'No results' or similar message is displayed.",
    ]
    return {"task_type": "amzn_help_center_topic", "topic": topic, "steps": steps}

_TASK_GENERATORS: Dict[AMZN_TASK_TYPES, Callable[[dict], dict]] = {
    "amzn_keyword_search": amzn_keyword_search,
    "amzn_location_search": amzn_location_search,
    "amzn_job_category_filter": amzn_job_category_filter,
    "amzn_team_filter": amzn_team_filter,
    "amzn_job_type_filter": amzn_job_type_filter,
    "amzn_apply_now_button": amzn_apply_now_button,
    "amzn_save_job_flow": amzn_save_job_flow,
    "amzn_job_description_assert": amzn_job_description_assert,
    "amzn_language_selector": amzn_language_selector,
    "amzn_help_center_topic": amzn_help_center_topic,
}

def generate_amzn_task(task_type: AMZN_TASK_TYPES, payload: dict) -> dict:
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
    items = list(AMZN_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_amzn_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)