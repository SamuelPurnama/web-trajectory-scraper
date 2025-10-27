import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

GLASSDOOR_TASK_TYPES = Literal[
    "gd_job_search",
    "gd_company_search",
    "gd_filter_location",
    "gd_filter_salary",
    "gd_filter_job_type",
    "gd_sort_by_date",
    "gd_view_job_details",
    "gd_view_company_reviews",
    "gd_signup_flow",
    "gd_login_negative",
    "gd_salary_search",
    "gd_browse_categories",
    "gd_filter_industry",
    "gd_filter_experience_level",
]

GLASSDOOR_SAMPLING_CONFIG: Dict[GLASSDOOR_TASK_TYPES, int] = {
    "gd_job_search": 10,
    "gd_company_search": 10,
    "gd_filter_location": 10,
    "gd_filter_salary": 10,
    "gd_filter_job_type": 10,
    "gd_sort_by_date": 10,
    "gd_view_job_details": 10,
    "gd_view_company_reviews": 10,
    "gd_signup_flow": 10,
    "gd_login_negative": 10,
    "gd_salary_search": 10,
    "gd_browse_categories": 10,
    "gd_filter_industry": 10,
    "gd_filter_experience_level": 10,
}

GD_JOB_TITLES = [
    "Software Engineer","Data Scientist","Product Manager","UX Designer","Business Analyst",
    "Accountant","Marketing Manager","Sales Representative","HR Coordinator","Financial Analyst",
    "Project Manager","DevOps Engineer","QA Engineer","Customer Service Representative","Operations Manager",
    "Graphic Designer","Mechanical Engineer","Electrical Engineer","Nurse","Pharmacist",
    "Civil Engineer","Web Developer","Content Writer","IT Support Specialist","Network Engineer"
]

GD_COMPANIES = [
    "Google","Amazon","Microsoft","Apple","Meta","IBM","Deloitte","Accenture","PwC","EY",
    "KPMG","Oracle","Salesforce","SAP","Uber","Airbnb","Tesla","Netflix","Adobe","Intel",
    "Cisco","Twitter","LinkedIn","Spotify","Zoom"
]

GD_LOCATIONS = [
    "New York, NY","San Francisco, CA","Seattle, WA","Chicago, IL","Austin, TX","Boston, MA","Los Angeles, CA",
    "Atlanta, GA","Dallas, TX","Denver, CO","Houston, TX","Washington, DC","San Diego, CA","Phoenix, AZ",
    "Philadelphia, PA","Charlotte, NC","Miami, FL","Minneapolis, MN","Portland, OR","Raleigh, NC",
    "Tampa, FL","Detroit, MI","Baltimore, MD","Salt Lake City, UT","Pittsburgh, PA"
]

GD_SALARY_RANGES = [
    "$40,000+","$50,000+","$60,000+","$70,000+","$80,000+","$90,000+","$100,000+","$110,000+","$120,000+",
    "$130,000+","$140,000+","$150,000+","$160,000+","$170,000+","$180,000+","$190,000+","$200,000+",
    "$210,000+","$220,000+","$230,000+","$240,000+","$250,000+"
]

GD_JOB_TYPES = [
    "Full-time","Part-time","Contract","Internship","Temporary","Commission","Volunteer","Per Diem","Seasonal",
    "Remote","On-site","Hybrid","Apprenticeship","Freelance","Entry Level","Mid Level","Senior Level",
    "Director","Executive","Hourly","Permanent","Consultant"
]

GD_INDUSTRIES = [
    "Technology","Finance","Healthcare","Retail","Education","Manufacturing","Consulting","Government",
    "Hospitality","Transportation","Media","Telecommunications","Real Estate","Energy","Pharmaceutical",
    "Automotive","Aerospace","Legal","Insurance","Food & Beverage","Construction","Nonprofit"
]

GD_EXPERIENCE_LEVELS = [
    "Internship","Entry Level","Associate","Mid Level","Senior Level","Manager","Director","Executive",
    "Lead","Principal","Junior","Trainee","Apprentice","Specialist","Consultant","Analyst","Coordinator",
    "Supervisor","Administrator","Advisor","Officer","Partner"
]

GD_CATEGORIES = [
    "Engineering","Business","Healthcare","Finance","Marketing","Sales","Operations","IT","Legal","Design",
    "Education","Customer Service","Human Resources","Science","Logistics","Construction","Media","Retail",
    "Hospitality","Real Estate","Transportation","Nonprofit"
]

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups, banners, or cookie notices.",
        "Do not submit any personal or payment information.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Glassdoor", steps).model_dump()

def gd_job_search(_: dict) -> dict:
    job = random.choice(GD_JOB_TITLES)
    steps = [
        "Go to url 'https://www.glassdoor.com/index.htm'.",
        *_ui_hygiene(),
        f"Focus the 'Job Title' search field.",
        f"Type '{job}' and select from autocomplete if available.",
        "Leave 'Location' as default.",
        "Click the 'Search' button.",
        f"Verify the results page shows jobs for '{job}'.",
        "Assert that at least one job card is visible.",
    ]
    return {"task_type":"gd_job_search","job_title":job,"steps":steps}

def gd_company_search(_: dict) -> dict:
    company = random.choice(GD_COMPANIES)
    steps = [
        "Go to url 'https://www.glassdoor.com/index.htm'.",
        *_ui_hygiene(),
        "Switch to the 'Companies' search tab.",
        f"Focus the 'Company' search field and type '{company}'.",
        "Select the company from autocomplete suggestions.",
        "Click the 'Search' button.",
        f"Verify the company page for '{company}' loads.",
        "Assert the company name is present in the page header.",
    ]
    return {"task_type":"gd_company_search","company":company,"steps":steps}

def gd_filter_location(_: dict) -> dict:
    job = random.choice(GD_JOB_TITLES)
    loc = random.choice(GD_LOCATIONS)
    steps = [
        "Go to url 'https://www.glassdoor.com/index.htm'.",
        *_ui_hygiene(),
        f"Focus the 'Job Title' search field and type '{job}'.",
        f"Focus the 'Location' field and type '{loc}'.",
        "Select from autocomplete if available.",
        "Click the 'Search' button.",
        f"Verify results are for '{job}' in '{loc}'.",
        "Assert at least one job card is visible.",
        "Check that the location filter shows '{loc}'.",
    ]
    return {"task_type":"gd_filter_location","job_title":job,"location":loc,"steps":steps}

def gd_filter_salary(_: dict) -> dict:
    job = random.choice(GD_JOB_TITLES)
    salary = random.choice(GD_SALARY_RANGES)
    steps = [
        "Go to url 'https://www.glassdoor.com/index.htm'.",
        *_ui_hygiene(),
        f"Search for '{job}' jobs (leave location default).",
        "On results page, open the 'Salary' filter.",
        f"Select '{salary}' as the minimum salary.",
        "Apply the filter.",
        f"Verify that all visible jobs list a salary >= {salary}.",
        "Assert at least one job card is visible.",
    ]
    return {"task_type":"gd_filter_salary","job_title":job,"salary_min":salary,"steps":steps}

def gd_filter_job_type(_: dict) -> dict:
    job = random.choice(GD_JOB_TITLES)
    job_type = random.choice(GD_JOB_TYPES)
    steps = [
        "Go to url 'https://www.glassdoor.com/index.htm'.",
        *_ui_hygiene(),
        f"Search for '{job}' jobs.",
        "On results page, open the 'Job Type' filter.",
        f"Select '{job_type}' and apply.",
        f"Verify that all visible jobs are '{job_type}' type.",
        "Assert at least one job card is visible.",
    ]
    return {"task_type":"gd_filter_job_type","job_title":job,"job_type":job_type,"steps":steps}

def gd_sort_by_date(_: dict) -> dict:
    job = random.choice(GD_JOB_TITLES)
    steps = [
        "Go to url 'https://www.glassdoor.com/index.htm'.",
        *_ui_hygiene(),
        f"Search for '{job}' jobs.",
        "On results page, locate the sort dropdown.",
        "Select 'Date Posted (Newest)' or equivalent.",
        "Verify the first job is the most recently posted.",
        "Assert at least one job card is visible.",
    ]
    return {"task_type":"gd_sort_by_date","job_title":job,"steps":steps}

def gd_view_job_details(_: dict) -> dict:
    job = random.choice(GD_JOB_TITLES)
    steps = [
        "Go to url 'https://www.glassdoor.com/index.htm'.",
        *_ui_hygiene(),
        f"Search for '{job}' jobs.",
        "On results page, click the first job card.",
        "Verify the job details pane or page loads.",
        "Assert the job title and company are visible.",
        "Check for an 'Apply' or 'Easy Apply' button.",
    ]
    return {"task_type":"gd_view_job_details","job_title":job,"steps":steps}

def gd_view_company_reviews(_: dict) -> dict:
    company = random.choice(GD_COMPANIES)
    steps = [
        "Go to url 'https://www.glassdoor.com/Reviews/index.htm'.",
        *_ui_hygiene(),
        f"Search for '{company}' in the company reviews search bar.",
        "Select the company from autocomplete.",
        "Verify the company reviews page loads.",
        "Assert at least one review is visible.",
        "Check that the company name appears in the header.",
    ]
    return {"task_type":"gd_view_company_reviews","company":company,"steps":steps}

def gd_signup_flow(_: dict) -> dict:
    email = f"testuser{random.randint(10000,99999)}@example.com"
    steps = [
        "Go to url 'https://www.glassdoor.com/profile/signup.htm'.",
        *_ui_hygiene(),
        "Fill in the 'Email' field with a valid email address.",
        "Fill in the 'Password' field with a strong password.",
        "Fill in the 'First Name' and 'Last Name' fields.",
        "Accept the terms and privacy policy.",
        "Click the 'Sign Up' button.",
        "Verify that a confirmation message or next step is shown.",
        "Assert that no error message is displayed for the email.",
    ]
    return {"task_type":"gd_signup_flow","email":email,"steps":steps}

def gd_login_negative(_: dict) -> dict:
    email = f"notareal{random.randint(10000,99999)}@example.com"
    steps = [
        "Go to url 'https://www.glassdoor.com/profile/login_input.htm'.",
        *_ui_hygiene(),
        f"Enter '{email}' in the 'Email' field.",
        "Enter an incorrect password.",
        "Click the 'Sign In' button.",
        "Verify that an error message is displayed indicating invalid credentials.",
        "Assert that the user is not logged in.",
    ]
    return {"task_type":"gd_login_negative","email":email,"steps":steps}

def gd_salary_search(_: dict) -> dict:
    job = random.choice(GD_JOB_TITLES)
    loc = random.choice(GD_LOCATIONS)
    steps = [
        "Go to url 'https://www.glassdoor.com/Salaries/index.htm'.",
        *_ui_hygiene(),
        f"Enter '{job}' in the 'Job Title' field.",
        f"Enter '{loc}' in the 'Location' field.",
        "Click the 'Search' button.",
        f"Verify that salary data for '{job}' in '{loc}' is displayed.",
        "Assert that at least one salary entry is visible.",
    ]
    return {"task_type":"gd_salary_search","job_title":job,"location":loc,"steps":steps}

def gd_browse_categories(_: dict) -> dict:
    cat = random.choice(GD_CATEGORIES)
    steps = [
        "Go to url 'https://www.glassdoor.com/Job/index.htm'.",
        *_ui_hygiene(),
        "Locate the 'Browse Jobs by Category' section.",
        f"Click on the '{cat}' category link.",
        f"Verify that the results page lists jobs in the '{cat}' category.",
        "Assert at least one job card is visible.",
    ]
    return {"task_type":"gd_browse_categories","category":cat,"steps":steps}

def gd_filter_industry(_: dict) -> dict:
    job = random.choice(GD_JOB_TITLES)
    industry = random.choice(GD_INDUSTRIES)
    steps = [
        "Go to url 'https://www.glassdoor.com/index.htm'.",
        *_ui_hygiene(),
        f"Search for '{job}' jobs.",
        "On results page, open the 'Industry' filter.",
        f"Select '{industry}' and apply.",
        f"Verify that all visible jobs are in the '{industry}' industry.",
        "Assert at least one job card is visible.",
    ]
    return {"task_type":"gd_filter_industry","job_title":job,"industry":industry,"steps":steps}

def gd_filter_experience_level(_: dict) -> dict:
    job = random.choice(GD_JOB_TITLES)
    exp = random.choice(GD_EXPERIENCE_LEVELS)
    steps = [
        "Go to url 'https://www.glassdoor.com/index.htm'.",
        *_ui_hygiene(),
        f"Search for '{job}' jobs.",
        "On results page, open the 'Experience Level' filter.",
        f"Select '{exp}' and apply.",
        f"Verify that all visible jobs are '{exp}' level.",
        "Assert at least one job card is visible.",
    ]
    return {"task_type":"gd_filter_experience_level","job_title":job,"experience_level":exp,"steps":steps}

_TASK_GENERATORS: Dict[GLASSDOOR_TASK_TYPES, Callable[[dict], dict]] = {
    "gd_job_search": gd_job_search,
    "gd_company_search": gd_company_search,
    "gd_filter_location": gd_filter_location,
    "gd_filter_salary": gd_filter_salary,
    "gd_filter_job_type": gd_filter_job_type,
    "gd_sort_by_date": gd_sort_by_date,
    "gd_view_job_details": gd_view_job_details,
    "gd_view_company_reviews": gd_view_company_reviews,
    "gd_signup_flow": gd_signup_flow,
    "gd_login_negative": gd_login_negative,
    "gd_salary_search": gd_salary_search,
    "gd_browse_categories": gd_browse_categories,
    "gd_filter_industry": gd_filter_industry,
    "gd_filter_experience_level": gd_filter_experience_level,
}

def generate_gd_task(task_type: GLASSDOOR_TASK_TYPES, payload: dict) -> dict:
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
    items = list(GLASSDOOR_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_gd_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)