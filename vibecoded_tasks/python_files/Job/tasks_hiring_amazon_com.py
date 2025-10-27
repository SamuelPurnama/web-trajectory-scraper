import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

AMZN_CITIES = [
    "Seattle", "New York", "San Francisco", "Austin", "Chicago", "Boston", "Los Angeles", "Dallas", "Nashville", "Atlanta",
    "Phoenix", "Denver", "Detroit", "Miami", "Minneapolis", "Portland", "San Diego", "Houston", "Baltimore", "Charlotte",
    "Philadelphia", "Tampa", "Columbus", "Indianapolis", "Orlando", "Salt Lake City", "Las Vegas", "Kansas City", "St. Louis", "Pittsburgh", "Raleigh"
]
AMZN_JOB_AREAS = [
    "Software Development", "Operations", "Customer Service", "Human Resources", "Finance", "Marketing", "Legal", "Design",
    "Product Management", "Sales", "Business Intelligence", "Data Science", "Cloud Computing", "Logistics", "Security",
    "Hardware Engineering", "Content Creation", "Public Relations", "Supply Chain", "Procurement", "Quality Assurance",
    "Retail", "Machine Learning", "AI Research", "Technical Writing"
]
AMZN_JOB_TYPES = [
    "Full Time", "Part Time", "Seasonal", "Internship", "Remote", "Onsite", "Contract", "Temporary", "Entry Level", "Experienced",
    "Manager", "Director", "Executive", "Hourly", "Salaried", "Graduate", "Apprenticeship", "Rotational", "Night Shift", "Weekend", "Flexible", "Hybrid"
]
AMZN_LANGUAGES = [
    "English", "Spanish", "French", "German", "Italian", "Portuguese", "Chinese", "Japanese", "Korean", "Russian", "Hindi",
    "Arabic", "Vietnamese", "Tagalog", "Polish", "Dutch", "Turkish", "Thai", "Hebrew", "Greek", "Czech", "Romanian"
]
AMZN_FILTERS = [
    "Remote Only", "Entry Level", "No Degree Required", "Veterans", "Disability Accommodations", "Flexible Hours", "Immediate Start",
    "Night Shifts", "Weekend Only", "Student Friendly", "Relocation Provided", "Sign-on Bonus", "Bilingual", "Warehouse", "Corporate",
    "Customer Facing", "Tech Roles", "Healthcare", "Transportation", "Management", "Leadership", "Amazon Fresh", "Prime Video", "AWS"
]
AMZN_FAQ_TOPICS = [
    "Application Status", "Interview Process", "Resume Tips", "Assessment Tests", "Background Checks", "Offer Letters",
    "Onboarding", "Work Authorization", "Relocation", "Remote Work", "Pay and Benefits", "Career Growth", "Diversity & Inclusion",
    "Disability Accommodations", "Veterans", "Student Programs", "Internships", "Dress Code", "COVID-19 Policy", "Job Alerts",
    "Technical Support", "Contact Us"
]
AMZN_SEARCH_TERMS = [
    "Software Engineer", "Warehouse Associate", "Data Analyst", "Customer Service", "Operations Manager", "Delivery Driver",
    "Product Designer", "Business Analyst", "Security Engineer", "Marketing Specialist", "Finance Manager", "HR Coordinator",
    "Cloud Architect", "Content Writer", "UX Researcher", "Logistics Planner", "Procurement Specialist", "QA Tester",
    "Retail Associate", "AI Scientist", "Machine Learning Engineer", "Supply Chain Analyst"
]
AMZN_SORT_OPTIONS = [
    "Relevance", "Date Posted", "Location", "Job Type", "Department", "Salary High-Low", "Salary Low-High", "Remote First",
    "Onsite First", "Entry Level First", "Most Popular", "Recently Added", "Alphabetical A-Z", "Alphabetical Z-A",
    "Flexible Hours", "Veteran Friendly", "Disability Friendly", "Internships", "Full Time", "Part Time", "Seasonal"
]
AMZN_LOCATIONS = [
    "Seattle, WA", "New York, NY", "San Francisco, CA", "Austin, TX", "Chicago, IL", "Boston, MA", "Los Angeles, CA", "Dallas, TX",
    "Nashville, TN", "Atlanta, GA", "Phoenix, AZ", "Denver, CO", "Detroit, MI", "Miami, FL", "Minneapolis, MN", "Portland, OR",
    "San Diego, CA", "Houston, TX", "Baltimore, MD", "Charlotte, NC", "Philadelphia, PA", "Tampa, FL", "Columbus, OH",
    "Indianapolis, IN", "Orlando, FL"
]
AMZN_DEPARTMENTS = [
    "Amazon Web Services", "Amazon Fresh", "Prime Video", "Amazon Logistics", "Amazon Studios", "Alexa", "Kindle", "Amazon Music",
    "Amazon Devices", "Amazon Retail", "Amazon Pharmacy", "Amazon Robotics", "Amazon Advertising", "Amazon Fashion",
    "Amazon Prime", "Amazon Go", "Amazon Air", "Amazon Pay", "Amazon Home Services", "Amazon Business", "Amazon Books"
]
AMZN_EDUCATION = [
    "No Degree", "High School", "Associate", "Bachelor's", "Master's", "PhD", "MBA", "JD", "Technical Certification",
    "Vocational Training", "Bootcamp Graduate", "GED", "Diploma", "Certificate", "Some College", "Professional License",
    "Trade School", "Military Training", "Online Course", "Apprenticeship", "Other"
]
AMZN_SALARY_RANGES = [
    "$15-20/hr", "$20-25/hr", "$25-30/hr", "$30-40/hr", "$40-50/hr", "$50-60/hr", "$60-80k", "$80-100k", "$100-120k", "$120-150k",
    "$150-200k", "$200k+", "Competitive", "DOE", "Negotiable", "Unspecified", "Commission", "Hourly", "Salaried", "Stipend", "Bonus Eligible"
]

AMZN_TASK_TYPES = Literal[
    "amzn_job_search",
    "amzn_job_filter",
    "amzn_job_sort",
    "amzn_job_details",
    "amzn_apply_now",
    "amzn_location_search",
    "amzn_language_filter",
    "amzn_faq_browse",
    "amzn_department_filter",
    "amzn_salary_filter",
    "amzn_education_filter"
]

AMZN_SAMPLING_CONFIG: Dict[AMZN_TASK_TYPES, int] = {
    "amzn_job_search": 10,
    "amzn_job_filter": 10,
    "amzn_job_sort": 10,
    "amzn_job_details": 10,
    "amzn_apply_now": 10,
    "amzn_location_search": 10,
    "amzn_language_filter": 10,
    "amzn_faq_browse": 10,
    "amzn_department_filter": 10,
    "amzn_salary_filter": 10,
    "amzn_education_filter": 10
}

def _rand_city():
    return random.choice(AMZN_CITIES)

def _rand_job_area():
    return random.choice(AMZN_JOB_AREAS)

def _rand_job_type():
    return random.choice(AMZN_JOB_TYPES)

def _rand_language():
    return random.choice(AMZN_LANGUAGES)

def _rand_filter():
    return random.choice(AMZN_FILTERS)

def _rand_faq_topic():
    return random.choice(AMZN_FAQ_TOPICS)

def _rand_search_term():
    return random.choice(AMZN_SEARCH_TERMS)

def _rand_sort_option():
    return random.choice(AMZN_SORT_OPTIONS)

def _rand_location():
    return random.choice(AMZN_LOCATIONS)

def _rand_department():
    return random.choice(AMZN_DEPARTMENTS)

def _rand_education():
    return random.choice(AMZN_EDUCATION)

def _rand_salary():
    return random.choice(AMZN_SALARY_RANGES)

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups, cookie banners, or location prompts if present.",
        "Do not submit any personal information or complete any purchases.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Amazon Hiring", steps).model_dump()

def amzn_job_search(_: dict) -> dict:
    term = _rand_search_term()
    steps = [
        "Go to url 'https://hiring.amazon.com'.",
        *_ui_hygiene(),
        "Ensure the job search input is visible.",
        f"Type '{term}' in the job search input.",
        "Press Enter or click the search button.",
        "Wait for results to load.",
        f"Assert that at least one job result contains '{term}' in the title or description.",
        "Check that the URL contains a search parameter matching the term.",
        "If no results, assert a 'no jobs found' message is visible.",
    ]
    return {
        "task_type": "amzn_job_search",
        "search_term": term,
        "steps": steps,
        "assertions": [
            f"At least one job result contains '{term}' or a 'no jobs found' message is shown.",
            "URL contains the search term as a parameter."
        ]
    }

def amzn_job_filter(_: dict) -> dict:
    filter_opt = _rand_filter()
    steps = [
        "Go to url 'https://hiring.amazon.com'.",
        *_ui_hygiene(),
        "Ensure the filters panel is visible.",
        f"Select the filter '{filter_opt}'.",
        "Wait for results to update.",
        f"Assert that all visible jobs match the '{filter_opt}' filter or that a 'no jobs found' message is shown.",
        "If available, clear the filter and verify the results change.",
    ]
    return {
        "task_type": "amzn_job_filter",
        "filter": filter_opt,
        "steps": steps,
        "assertions": [
            f"All results match the '{filter_opt}' filter or a 'no jobs found' message is shown.",
            "Clearing the filter updates the results."
        ]
    }

def amzn_job_sort(_: dict) -> dict:
    sort_opt = _rand_sort_option()
    steps = [
        "Go to url 'https://hiring.amazon.com'.",
        *_ui_hygiene(),
        "Ensure the sort dropdown is visible.",
        f"Select the sort option '{sort_opt}'.",
        "Wait for results to update.",
        f"Assert that job results are sorted by '{sort_opt}'.",
        "If possible, select a different sort option and verify the order changes.",
    ]
    return {
        "task_type": "amzn_job_sort",
        "sort_option": sort_opt,
        "steps": steps,
        "assertions": [
            f"Results are sorted by '{sort_opt}'.",
            "Changing sort option changes the order."
        ]
    }

def amzn_job_details(_: dict) -> dict:
    term = _rand_search_term()
    steps = [
        "Go to url 'https://hiring.amazon.com'.",
        *_ui_hygiene(),
        f"Search for '{term}' in the job search input and submit.",
        "Wait for results to load.",
        "Click on the first job result.",
        "Wait for the job details page to load.",
        "Assert that the job title, location, and description are visible.",
        "Assert that an 'Apply Now' button is present.",
        "Assert that the URL contains a job ID or slug.",
    ]
    return {
        "task_type": "amzn_job_details",
        "search_term": term,
        "steps": steps,
        "assertions": [
            "Job title, location, and description are visible.",
            "'Apply Now' button is present.",
            "URL contains a job ID or slug."
        ]
    }

def amzn_apply_now(_: dict) -> dict:
    term = _rand_search_term()
    steps = [
        "Go to url 'https://hiring.amazon.com'.",
        *_ui_hygiene(),
        f"Search for '{term}' in the job search input and submit.",
        "Wait for results to load.",
        "Click on the first job result.",
        "Wait for the job details page to load.",
        "Click the 'Apply Now' button.",
        "Wait for the application form to appear.",
        "Assert that the application form fields (name, email, phone, resume upload) are visible.",
        "Do not submit the form.",
        "Assert that the application page URL is correct.",
    ]
    return {
        "task_type": "amzn_apply_now",
        "search_term": term,
        "steps": steps,
        "assertions": [
            "Application form fields are visible.",
            "Application page URL is correct."
        ]
    }

def amzn_location_search(_: dict) -> dict:
    location = _rand_location()
    steps = [
        "Go to url 'https://hiring.amazon.com'.",
        *_ui_hygiene(),
        "Ensure the location filter/input is visible.",
        f"Type/select '{location}' in the location filter.",
        "Wait for results to update.",
        f"Assert that all visible jobs are in '{location}' or a 'no jobs found' message is shown.",
        "If available, clear the location filter and verify the results change.",
    ]
    return {
        "task_type": "amzn_location_search",
        "location": location,
        "steps": steps,
        "assertions": [
            f"All results are in '{location}' or a 'no jobs found' message is shown.",
            "Clearing the location filter updates the results."
        ]
    }

def amzn_language_filter(_: dict) -> dict:
    language = _rand_language()
    steps = [
        "Go to url 'https://hiring.amazon.com'.",
        *_ui_hygiene(),
        "Open the language filter or advanced search.",
        f"Select '{language}' as the language requirement.",
        "Wait for results to update.",
        f"Assert that all visible jobs require or support '{language}', or a 'no jobs found' message is shown.",
        "If available, clear the language filter and verify the results change.",
    ]
    return {
        "task_type": "amzn_language_filter",
        "language": language,
        "steps": steps,
        "assertions": [
            f"All results require/support '{language}' or a 'no jobs found' message is shown.",
            "Clearing the language filter updates the results."
        ]
    }

def amzn_faq_browse(_: dict) -> dict:
    topic = _rand_faq_topic()
    steps = [
        "Go to url 'https://hiring.amazon.com'.",
        *_ui_hygiene(),
        "Scroll to or open the FAQ/help/support section.",
        f"Find and open the FAQ topic '{topic}'.",
        "Assert that the topic content is visible.",
        "Assert that at least one answer or paragraph is shown.",
        "If available, use the FAQ search to search for the topic and verify it appears in results.",
    ]
    return {
        "task_type": "amzn_faq_browse",
        "faq_topic": topic,
        "steps": steps,
        "assertions": [
            f"FAQ topic '{topic}' content is visible.",
            "At least one answer or paragraph is shown."
        ]
    }

def amzn_department_filter(_: dict) -> dict:
    department = _rand_department()
    steps = [
        "Go to url 'https://hiring.amazon.com'.",
        *_ui_hygiene(),
        "Open the department filter or advanced search.",
        f"Select '{department}' as the department.",
        "Wait for results to update.",
        f"Assert that all visible jobs are in the '{department}' department or a 'no jobs found' message is shown.",
        "If available, clear the department filter and verify the results change.",
    ]
    return {
        "task_type": "amzn_department_filter",
        "department": department,
        "steps": steps,
        "assertions": [
            f"All results are in '{department}' or a 'no jobs found' message is shown.",
            "Clearing the department filter updates the results."
        ]
    }

def amzn_salary_filter(_: dict) -> dict:
    salary = _rand_salary()
    steps = [
        "Go to url 'https://hiring.amazon.com'.",
        *_ui_hygiene(),
        "Open the salary filter or advanced search.",
        f"Select '{salary}' as the salary range.",
        "Wait for results to update.",
        f"Assert that all visible jobs list a salary matching '{salary}' or a 'no jobs found' message is shown.",
        "If available, clear the salary filter and verify the results change.",
    ]
    return {
        "task_type": "amzn_salary_filter",
        "salary_range": salary,
        "steps": steps,
        "assertions": [
            f"All results list salary '{salary}' or a 'no jobs found' message is shown.",
            "Clearing the salary filter updates the results."
        ]
    }

def amzn_education_filter(_: dict) -> dict:
    education = _rand_education()
    steps = [
        "Go to url 'https://hiring.amazon.com'.",
        *_ui_hygiene(),
        "Open the education filter or advanced search.",
        f"Select '{education}' as the required education level.",
        "Wait for results to update.",
        f"Assert that all visible jobs require '{education}' or a 'no jobs found' message is shown.",
        "If available, clear the education filter and verify the results change.",
    ]
    return {
        "task_type": "amzn_education_filter",
        "education_level": education,
        "steps": steps,
        "assertions": [
            f"All results require '{education}' or a 'no jobs found' message is shown.",
            "Clearing the education filter updates the results."
        ]
    }

_TASK_GENERATORS: Dict[AMZN_TASK_TYPES, Callable[[dict], dict]] = {
    "amzn_job_search": amzn_job_search,
    "amzn_job_filter": amzn_job_filter,
    "amzn_job_sort": amzn_job_sort,
    "amzn_job_details": amzn_job_details,
    "amzn_apply_now": amzn_apply_now,
    "amzn_location_search": amzn_location_search,
    "amzn_language_filter": amzn_language_filter,
    "amzn_faq_browse": amzn_faq_browse,
    "amzn_department_filter": amzn_department_filter,
    "amzn_salary_filter": amzn_salary_filter,
    "amzn_education_filter": amzn_education_filter
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