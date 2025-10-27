import json
import random
import datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

INDEED_TASK_TYPES = Literal[
    "indeed_job_search",
    "indeed_job_search_filter_location",
    "indeed_job_search_filter_category",
    "indeed_job_search_sort",
    "indeed_clear_location",
    "indeed_company_search",
    "indeed_browse_industry",
    "indeed_browse_company_details",
    "indeed_salary_search",
    "indeed_salary_filter_industry",
    "indeed_salary_top_jobs",
    "indeed_footer_navigation",
    "indeed_employer_rating",
    "indeed_language_switch",
]

INDEED_SAMPLING_CONFIG: Dict[INDEED_TASK_TYPES, int] = {
    "indeed_job_search": 10,
    "indeed_job_search_filter_location": 10,
    "indeed_job_search_filter_category": 10,
    "indeed_job_search_sort": 10,
    "indeed_clear_location": 10,
    "indeed_company_search": 10,
    "indeed_browse_industry": 10,
    "indeed_browse_company_details": 10,
    "indeed_salary_search": 10,
    "indeed_salary_filter_industry": 10,
    "indeed_salary_top_jobs": 10,
    "indeed_footer_navigation": 10,
    "indeed_employer_rating": 10,
    "indeed_language_switch": 10,
}

JOB_TITLES = [
    "Software Engineer", "Project Manager", "Data Analyst", "Registered Nurse", "Sales Associate",
    "Customer Service Representative", "Accountant", "Marketing Manager", "Business Analyst", "HR Coordinator",
    "Administrative Assistant", "Graphic Designer", "Mechanical Engineer", "Operations Manager", "Financial Analyst",
    "Pharmacist", "Web Developer", "Teacher", "Electrician", "Truck Driver",
    "Warehouse Worker", "Receptionist", "Medical Assistant", "IT Support Specialist", "Product Manager",
    "UX Designer", "Civil Engineer", "Quality Assurance Analyst", "Store Manager", "Research Scientist"
]

CITIES = [
    "New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX", "Phoenix, AZ",
    "Philadelphia, PA", "San Antonio, TX", "San Diego, CA", "Dallas, TX", "San Jose, CA",
    "Austin, TX", "Jacksonville, FL", "Fort Worth, TX", "Columbus, OH", "Charlotte, NC",
    "San Francisco, CA", "Indianapolis, IN", "Seattle, WA", "Denver, CO", "Washington, DC",
    "Boston, MA", "El Paso, TX", "Nashville, TN", "Detroit, MI", "Oklahoma City, OK",
    "Portland, OR", "Las Vegas, NV", "Memphis, TN", "Louisville, KY", "Baltimore, MD"
]

INDUSTRIES = [
    "Aerospace & Defense", "Agriculture", "Automotive", "Banking & Finance", "Biotechnology",
    "Construction", "Consumer Goods", "Education", "Energy", "Engineering",
    "Entertainment", "Environmental", "Government", "Healthcare", "Hospitality",
    "Information Technology", "Insurance", "Legal", "Manufacturing", "Media",
    "Nonprofit", "Pharmaceutical", "Real Estate", "Retail", "Telecommunications",
    "Transportation", "Travel & Tourism", "Utilities", "Wholesale", "Food & Beverage"
]

COMPANIES = [
    "Amazon", "Google", "Microsoft", "Apple", "Facebook", "Tesla", "Walmart", "The Home Depot", "Target", "CVS Health",
    "Kroger", "Costco", "Walgreens", "Starbucks", "McDonald's", "Boeing", "Ford", "General Motors", "JPMorgan Chase", "Bank of America",
    "Wells Fargo", "UnitedHealth Group", "Cigna", "AT&T", "Verizon", "Comcast", "FedEx", "UPS", "Delta Air Lines", "American Airlines"
]

FOOTER_LINKS = [
    ("Hiring Lab", "https://www.indeed.com/hiring-lab"),
    ("Career advice", "https://www.indeed.com/career-advice"),
    ("Browse jobs", "https://www.indeed.com/browsejobs"),
    ("Browse companies", "https://www.indeed.com/companies"),
    ("Salaries", "https://www.indeed.com/salaries"),
    ("Indeed Events", "https://www.indeed.com/events"),
    ("Work at Indeed", "https://www.indeed.jobs/"),
    ("Countries", "https://www.indeed.com/worldwide"),
    ("About", "https://www.indeed.com/about"),
    ("Help", "https://www.indeed.com/help"),
    ("ESG at Indeed", "https://www.indeed.com/esg"),
    ("Your Privacy Choices", "https://www.indeed.com/privacy"),
    ("Accessibility at Indeed", "https://www.indeed.com/accessibility"),
    ("Privacy Center and Ad Choices", "https://www.indeed.com/legal"),
    ("Terms", "https://www.indeed.com/legal"),
    ("Career Explorer", "https://www.indeed.com/career"),
    ("Contact us", "https://www.indeed.com/contact"),
    ("Post a job", "https://www.indeed.com/hire"),
    ("Find jobs", "https://www.indeed.com/jobs"),
    ("Upload your resume", "https://www.indeed.com/create-resume")
]

LANGUAGES = [
    "English", "Español", "Français", "Deutsch", "Português", "Italiano", "Nederlands", "Polski", "Türkçe", "Svenska",
    "Norsk", "Dansk", "Suomi", "Русский", "中文", "日本語", "한국어", "العربية", "עברית", "ไทย",
    "Bahasa Indonesia", "Čeština", "Magyar", "Ελληνικά", "Română"
]

EMPLOYER_RATINGS = [1, 2, 3, 4, 5]

SALARY_JOB_TITLES = [
    "Software Engineer", "Registered Nurse", "Data Scientist", "Teacher", "Project Manager",
    "Accountant", "Mechanical Engineer", "Pharmacist", "Web Developer", "Financial Analyst",
    "Business Analyst", "Graphic Designer", "Operations Manager", "Civil Engineer", "Sales Manager",
    "HR Manager", "Marketing Specialist", "IT Support Specialist", "Product Manager", "Store Manager",
    "Truck Driver", "Medical Assistant", "Receptionist", "Warehouse Worker", "Quality Assurance Analyst"
]

SALARY_LOCATIONS = [
    "United States", "California", "Texas", "Florida", "New York", "Illinois", "Pennsylvania", "Ohio", "Georgia", "North Carolina",
    "Michigan", "New Jersey", "Virginia", "Washington", "Arizona", "Massachusetts", "Tennessee", "Indiana", "Missouri", "Maryland"
]

SALARY_INDUSTRIES = [
    "All Industries", "Healthcare", "Technology", "Finance", "Education", "Retail", "Manufacturing", "Transportation", "Construction", "Hospitality",
    "Energy", "Government", "Telecommunications", "Pharmaceutical", "Legal", "Insurance", "Real Estate", "Media", "Nonprofit", "Agriculture"
]

SORT_OPTIONS = [
    "Relevance", "Date", "Salary (Highest)", "Salary (Lowest)", "Distance", "Company", "Job Title", "Location", "Experience Level", "Remote",
    "Full-time", "Part-time", "Contract", "Internship", "Temporary", "Commission", "Shift", "Night Shift", "Weekend", "Urgently Hiring"
]

def _rand_job_title() -> str:
    return random.choice(JOB_TITLES)

def _rand_city() -> str:
    return random.choice(CITIES)

def _rand_industry() -> str:
    return random.choice(INDUSTRIES)

def _rand_company() -> str:
    return random.choice(COMPANIES)

def _rand_footer_link() -> tuple:
    return random.choice(FOOTER_LINKS)

def _rand_language() -> str:
    return random.choice(LANGUAGES)

def _rand_employer_rating() -> int:
    return random.choice(EMPLOYER_RATINGS)

def _rand_salary_job_title() -> str:
    return random.choice(SALARY_JOB_TITLES)

def _rand_salary_location() -> str:
    return random.choice(SALARY_LOCATIONS)

def _rand_salary_industry() -> str:
    return random.choice(SALARY_INDUSTRIES)

def _rand_sort_option() -> str:
    return random.choice(SORT_OPTIONS)

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups or banners (e.g., 'Your browser is out of date', 'Watch out for suspicious messages').",
        "Do not sign in or create an account unless specifically required.",
        "Do not upload a resume or submit any personal information.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Indeed", steps).model_dump()

def indeed_job_search(_: dict) -> dict:
    job_title = _rand_job_title()
    steps = [
        "Go to url 'https://www.indeed.com'.",
        *_ui_hygiene(),
        "Focus the combobox labeled 'search: Job title, keywords, or company'.",
        "Clear any existing text.",
        f"Type '{job_title}'.",
        "Ensure the location field contains a valid city or region.",
        "Click the 'Search' button.",
        "Wait for the job results page to load.",
        f"Assert that the results page contains job listings for '{job_title}'.",
    ]
    return {
        "task_type": "indeed_job_search",
        "job_title": job_title,
        "steps": steps,
        "assertion": f"At least one job listing for '{job_title}' is visible in the results.",
    }

def indeed_job_search_filter_location(_: dict) -> dict:
    job_title = _rand_job_title()
    city = _rand_city()
    steps = [
        "Go to url 'https://www.indeed.com'.",
        *_ui_hygiene(),
        "Focus the combobox labeled 'search: Job title, keywords, or company'.",
        "Clear any existing text.",
        f"Type '{job_title}'.",
        "Focus the combobox labeled 'Edit location'.",
        "Clear any existing text.",
        f"Type '{city}'.",
        "Select the location from the autocomplete dropdown if available.",
        "Click the 'Search' button.",
        "Wait for the job results page to load.",
        f"Assert that the results page contains job listings for '{job_title}' in '{city}'.",
    ]
    return {
        "task_type": "indeed_job_search_filter_location",
        "job_title": job_title,
        "location": city,
        "steps": steps,
        "assertion": f"At least one job listing for '{job_title}' in '{city}' is visible in the results.",
    }

def indeed_job_search_filter_category(_: dict) -> dict:
    job_title = _rand_job_title()
    industry = _rand_industry()
    steps = [
        "Go to url 'https://www.indeed.com'.",
        *_ui_hygiene(),
        "Focus the combobox labeled 'search: Job title, keywords, or company'.",
        "Clear any existing text.",
        f"Type '{job_title}'.",
        "Ensure the location field contains a valid city or region.",
        "Click the 'Search' button.",
        "Wait for the job results page to load.",
        f"Locate and open the filter for 'Industry' or 'Category'.",
        f"Select '{industry}' from the list of industries.",
        "Apply the filter.",
        f"Assert that the results page contains job listings for '{job_title}' in the '{industry}' industry.",
    ]
    return {
        "task_type": "indeed_job_search_filter_category",
        "job_title": job_title,
        "industry": industry,
        "steps": steps,
        "assertion": f"At least one job listing for '{job_title}' in the '{industry}' industry is visible.",
    }

def indeed_job_search_sort(_: dict) -> dict:
    job_title = _rand_job_title()
    sort_option = _rand_sort_option()
    steps = [
        "Go to url 'https://www.indeed.com'.",
        *_ui_hygiene(),
        "Focus the combobox labeled 'search: Job title, keywords, or company'.",
        "Clear any existing text.",
        f"Type '{job_title}'.",
        "Ensure the location field contains a valid city or region.",
        "Click the 'Search' button.",
        "Wait for the job results page to load.",
        "Locate the sort dropdown on the results page.",
        f"Select the '{sort_option}' option.",
        "Wait for the results to update.",
        f"Assert that the job listings are sorted by '{sort_option}'.",
    ]
    return {
        "task_type": "indeed_job_search_sort",
        "job_title": job_title,
        "sort_option": sort_option,
        "steps": steps,
        "assertion": f"Job results are sorted by '{sort_option}'.",
    }

def indeed_clear_location(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.indeed.com'.",
        *_ui_hygiene(),
        "Focus the combobox labeled 'Edit location'.",
        "Clear any existing text.",
        "Click the 'Clear location input' button.",
        "Assert that the location field is empty.",
        "Focus the job search field and type 'Project Manager'.",
        "Click the 'Search' button.",
        "Wait for the results page to load.",
        "Assert that the results are not restricted to any specific city.",
    ]
    return {
        "task_type": "indeed_clear_location",
        "steps": steps,
        "assertion": "Location field is empty and search results are not location-filtered.",
    }

def indeed_company_search(_: dict) -> dict:
    company = _rand_company()
    steps = [
        "Go to url 'https://www.indeed.com/companies'.",
        *_ui_hygiene(),
        "Focus the combobox labeled 'Company name or job title'.",
        "Clear any existing text.",
        f"Type '{company}'.",
        "Click the 'Find Companies' button.",
        "Wait for the company results page to load.",
        f"Assert that '{company}' appears in the company search results.",
    ]
    return {
        "task_type": "indeed_company_search",
        "company": company,
        "steps": steps,
        "assertion": f"Company '{company}' is listed in the search results.",
    }

def indeed_browse_industry(_: dict) -> dict:
    industry = _rand_industry()
    steps = [
        "Go to url 'https://www.indeed.com/companies'.",
        *_ui_hygiene(),
        "Scroll to the 'Browse by industry' section.",
        "If not visible, click the 'See all industries' button.",
        f"Click the link for '{industry}'.",
        "Wait for the industry company list page to load.",
        f"Assert that companies in the '{industry}' industry are listed.",
    ]
    return {
        "task_type": "indeed_browse_industry",
        "industry": industry,
        "steps": steps,
        "assertion": f"Companies in the '{industry}' industry are displayed.",
    }

def indeed_browse_company_details(_: dict) -> dict:
    company = _rand_company()
    section = random.choice(["Reviews", "Salaries", "Q&A", "Open jobs"])
    steps = [
        "Go to url 'https://www.indeed.com/companies'.",
        *_ui_hygiene(),
        "Scroll to the 'Popular companies' section.",
        f"Click the link for '{company}'.",
        "Wait for the company profile page to load.",
        f"Navigate to the '{section}' section/tab.",
        f"Assert that the '{section}' section for '{company}' is displayed.",
    ]
    return {
        "task_type": "indeed_browse_company_details",
        "company": company,
        "section": section,
        "steps": steps,
        "assertion": f"Section '{section}' for company '{company}' is visible.",
    }

def indeed_salary_search(_: dict) -> dict:
    job_title = _rand_salary_job_title()
    location = _rand_salary_location()
    steps = [
        "Go to url 'https://www.indeed.com/career/salaries'.",
        *_ui_hygiene(),
        "Focus the textbox labeled 'Job title'.",
        "Clear any existing text.",
        f"Type '{job_title}'.",
        "Focus the textbox labeled 'Where'.",
        "Clear any existing text.",
        f"Type '{location}'.",
        "Click the 'Search' button (if enabled).",
        "Wait for the salary results page to load.",
        f"Assert that salary information for '{job_title}' in '{location}' is displayed.",
    ]
    return {
        "task_type": "indeed_salary_search",
        "job_title": job_title,
        "location": location,
        "steps": steps,
        "assertion": f"Salary data for '{job_title}' in '{location}' is shown.",
    }

def indeed_salary_filter_industry(_: dict) -> dict:
    industry = _rand_salary_industry()
    steps = [
        "Go to url 'https://www.indeed.com/career/salaries'.",
        *_ui_hygiene(),
        "Locate the industry filter combobox.",
        f"Select '{industry}' from the dropdown.",
        "Wait for the salary data to update.",
        f"Assert that the salary data is filtered for '{industry}'.",
    ]
    return {
        "task_type": "indeed_salary_filter_industry",
        "industry": industry,
        "steps": steps,
        "assertion": f"Salary data is filtered for industry '{industry}'.",
    }

def indeed_salary_top_jobs(_: dict) -> dict:
    job_title = _rand_salary_job_title()
    steps = [
        "Go to url 'https://www.indeed.com/career/salaries'.",
        *_ui_hygiene(),
        "Scroll to the 'Explore top paying jobs' section.",
        f"Click the link for '{job_title}'.",
        "Wait for the job salary details page to load.",
        f"Assert that salary details for '{job_title}' are displayed.",
    ]
    return {
        "task_type": "indeed_salary_top_jobs",
        "job_title": job_title,
        "steps": steps,
        "assertion": f"Salary details for '{job_title}' are visible.",
    }

def indeed_footer_navigation(_: dict) -> dict:
    link_name, link_url = _rand_footer_link()
    steps = [
        "Go to url 'https://www.indeed.com'.",
        *_ui_hygiene(),
        "Scroll to the footer section.",
        f"Click the link labeled '{link_name}'.",
        f"Wait for the page to navigate to '{link_url}'.",
        f"Assert that the current URL is '{link_url}'.",
    ]
    return {
        "task_type": "indeed_footer_navigation",
        "footer_link": link_name,
        "footer_url": link_url,
        "steps": steps,
        "assertion": f"Current URL is '{link_url}'.",
    }

def indeed_employer_rating(_: dict) -> dict:
    rating = _rand_employer_rating()
    steps = [
        "Go to url 'https://www.indeed.com/companies'.",
        *_ui_hygiene(),
        "Scroll to the 'Rate your recent employer' section.",
        f"Click the link labeled '{rating} star out of 5'.",
        "If a feedback form appears, do not submit; just verify the rating selection.",
        f"Assert that the '{rating} star out of 5' selection is highlighted.",
    ]
    return {
        "task_type": "indeed_employer_rating",
        "rating": rating,
        "steps": steps,
        "assertion": f"'{rating} star out of 5' is selected/highlighted.",
    }

def indeed_language_switch(_: dict) -> dict:
    language = _rand_language()
    steps = [
        "Go to url 'https://www.indeed.com'.",
        *_ui_hygiene(),
        "Scroll to the bottom of the page.",
        "Locate the language switcher (e.g., link labeled 'español' or similar).",
        f"Click the link or button to switch to '{language}'.",
        f"Wait for the page to reload in '{language}' (if supported).",
        f"Assert that the page content or navigation is now displayed in '{language}' or that a language indicator is visible.",
    ]
    return {
        "task_type": "indeed_language_switch",
        "language": language,
        "steps": steps,
        "assertion": f"Page is displayed in '{language}' or language indicator is set.",
    }

_TASK_GENERATORS: Dict[INDEED_TASK_TYPES, Callable[[dict], dict]] = {
    "indeed_job_search": indeed_job_search,
    "indeed_job_search_filter_location": indeed_job_search_filter_location,
    "indeed_job_search_filter_category": indeed_job_search_filter_category,
    "indeed_job_search_sort": indeed_job_search_sort,
    "indeed_clear_location": indeed_clear_location,
    "indeed_company_search": indeed_company_search,
    "indeed_browse_industry": indeed_browse_industry,
    "indeed_browse_company_details": indeed_browse_company_details,
    "indeed_salary_search": indeed_salary_search,
    "indeed_salary_filter_industry": indeed_salary_filter_industry,
    "indeed_salary_top_jobs": indeed_salary_top_jobs,
    "indeed_footer_navigation": indeed_footer_navigation,
    "indeed_employer_rating": indeed_employer_rating,
    "indeed_language_switch": indeed_language_switch,
}

def generate_indeed_task(task_type: INDEED_TASK_TYPES, payload: dict) -> dict:
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
    items = list(INDEED_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_indeed_task, ttype, p))
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