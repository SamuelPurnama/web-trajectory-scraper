import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

CHRONICLE_TASK_TYPES = Literal[
    "chronicle_keyword_search",
    "chronicle_location_search",
    "chronicle_category_browse",
    "chronicle_position_type_filter",
    "chronicle_distance_filter",
    "chronicle_top_job_details",
    "chronicle_featured_employer_browse",
    "chronicle_create_account_flow",
    "chronicle_job_alerts_flow",
    "chronicle_resume_upload_flow",
    "chronicle_career_resources_article",
    "chronicle_popular_searches",
    "chronicle_employer_links",
    "chronicle_support_links",
]

CHRONICLE_SAMPLING_CONFIG: Dict[CHRONICLE_TASK_TYPES, int] = {
    "chronicle_keyword_search": 10,
    "chronicle_location_search": 10,
    "chronicle_category_browse": 10,
    "chronicle_position_type_filter": 10,
    "chronicle_distance_filter": 10,
    "chronicle_top_job_details": 10,
    "chronicle_featured_employer_browse": 10,
    "chronicle_create_account_flow": 10,
    "chronicle_job_alerts_flow": 10,
    "chronicle_resume_upload_flow": 10,
    "chronicle_career_resources_article": 10,
    "chronicle_popular_searches": 10,
    "chronicle_employer_links": 10,
    "chronicle_support_links": 10,
}

KEYWORDS = [
    "biology", "mathematics", "engineering", "psychology", "art", "history", "finance", "marketing", "nursing",
    "chemistry", "physics", "music", "law", "education", "computer science", "business", "counseling", "economics",
    "philosophy", "athletics", "communications", "design", "social work", "research", "humanities", "enrollment",
    "development", "health", "security", "dean", "president"
][:25]

LOCATIONS = [
    "New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX", "Phoenix, AZ", "Philadelphia, PA",
    "San Antonio, TX", "San Diego, CA", "Dallas, TX", "San Jose, CA", "Austin, TX", "Jacksonville, FL",
    "Fort Worth, TX", "Columbus, OH", "Charlotte, NC", "San Francisco, CA", "Indianapolis, IN", "Seattle, WA",
    "Denver, CO", "Washington, DC", "Boston, MA", "El Paso, TX", "Nashville, TN", "Detroit, MI", "Oklahoma City, OK"
][:25]

DISTANCES = [
    "Within 0 miles", "Within 5 miles", "Within 10 miles", "Within 15 miles", "Within 20 miles",
    "Within 25 miles", "Within 30 miles", "Within 35 miles", "Within 40 miles", "Within 45 miles",
    "Within 50 miles", "Within 60 miles", "Within 70 miles", "Within 80 miles", "Within 90 miles",
    "Within 100 miles", "Within 125 miles", "Within 150 miles", "Within 200 miles", "Within 250 miles"
]

CATEGORIES = [
    "Academic Advising & Academic Support Services",
    "Academic Affairs",
    "Accounting & Finance",
    "Admissions",
    "Agriculture & Animal Sciences",
    "Art History",
    "Arts",
    "Athletics",
    "Biology & Life Sciences",
    "Business & Administrative Affairs",
    "Business & Management",
    "Campus Security/Police",
    "Chancellors & Presidents",
    "Chemistry",
    "Chief Academic Officers & Provosts",
    "Communications",
    "Computer Sciences & Technology",
    "Counseling",
    "Criminal Justice & Criminology",
    "Deans",
    "Design & Graphic Arts",
    "Development & Advancement",
    "Economics",
    "Education",
    "Engineering",
    "English & Literature",
    "Enrollment Management",
    "Executive Directors",
    "Facilities",
    "Faculty Affairs",
    "Financial Aid",
    "Foreign Languages & Literatures",
    "Grants & Contracts",
    "Health Sciences",
    "Health Services",
    "History",
    "Humanities",
    "IT & Technology",
    "Law & Legal Studies",
    "Legal Affairs",
    "Librarians & Library Administration",
    "Marketing & Sales",
    "Mathematics",
    "Medicine",
    "Music",
    "Nursing",
    "Performing Arts",
    "Philosophy",
    "Physics & Space Sciences",
    "Psychology",
    "Research Administration",
    "Residence Life",
    "Science & Mathematics",
    "Social & Behavioral Sciences",
    "Social Work & Human Services",
    "Student Affairs",
    "Vice Presidents",
    "Vocational & Technical Fields"
][:35]

POSITION_TYPES = [
    "ADMINISTRATIVE JOBS", "EXECUTIVE JOBS", "FACULTY POSITIONS", "JOBS OUTSIDE ACADEME"
]

TOP_JOB_TITLES = [
    "Ramapo College of NJ - Tenure Track Faculty Openings for 2026/2027 Academic Year",
    "Tenure Track positions in Microbiology, Genomics, and Bioinformatics",
    "FACULTY FELLOW IN ASIAN/PACIFIC/AMERICAN STUDIES",
    "Research & Instruction Librarian and Assistant Professor",
    "Professor jobs in higher education",
    "Adjunct jobs in higher education",
    "Adjunct jobs in Washington D.C.",
    "Remote jobs in higher education",
    "Academic Affairs",
    "Engineering"
][:10]

FEATURED_EMPLOYERS = [
    "Lander University",
    "Texas Tech University - Health Sciences Center",
    "St. Charles Community College",
    "University of New England",
    "University of Indianapolis",
    "Empire State University SUNY",
    "Ramapo College of NJ",
    "University of Texas, Arlington",
    "New York University Arts and Science",
    "University of Mississippi",
    "University of New England",
    "University of Indianapolis",
    "Empire State University SUNY",
    "St. Charles Community College",
    "Texas Tech University - Health Sciences Center",
    "Lander University",
    "University of Mississippi",
    "Ramapo College of NJ",
    "New York University Arts and Science",
    "University of Texas, Arlington"
]

CAREER_RESOURCES = [
    "How to Start Off Right in Your New Job",
    "Preparing to Take Office",
    "Your First Day on the Job as an Interim Leader"
]

POPULAR_SEARCHES = [
    "Adjunct jobs in higher education",
    "Professor jobs in higher education",
    "Adjunct jobs in Washington D.C.",
    "Remote jobs in higher education"
]

EMPLOYER_LINKS = [
    "Post a Job",
    "Pricing",
    "Issue Dates & Deadlines",
    "Rate Card",
    "Create an Account"
]

SUPPORT_LINKS = [
    "About Us",
    "Contact Us",
    "Terms & Conditions",
    "Privacy Policy",
    "User Agreement",
    "Accessibility Statement"
]

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups or banners (e.g., cookie notices, newsletter signups).",
        "Do not submit any personal information or complete any purchases.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Chronicle", steps).model_dump()

def chronicle_keyword_search(_: dict) -> dict:
    keyword = random.choice(KEYWORDS)
    steps = [
        "Go to url 'https://jobs.chronicle.com'.",
        *_ui_hygiene(),
        "Locate the 'KEYWORDS' textbox.",
        f"Enter '{keyword}' into the 'KEYWORDS' field.",
        "Leave the 'LOCATION' field blank.",
        "Click the 'Find jobs' button.",
        f"Verify that search results are shown and at least one result contains '{keyword}' (case-insensitive) in the job title or description.",
        "Assert that the URL contains a query string with the keyword.",
        "If no results, verify a 'no jobs found' message is displayed."
    ]
    return {"task_type": "chronicle_keyword_search", "keyword": keyword, "steps": steps}

def chronicle_location_search(_: dict) -> dict:
    location = random.choice(LOCATIONS)
    steps = [
        "Go to url 'https://jobs.chronicle.com'.",
        *_ui_hygiene(),
        "Locate the 'LOCATION' combobox.",
        f"Enter or select '{location}' in the 'LOCATION' field.",
        "Leave the 'KEYWORDS' field blank.",
        "Click the 'Find jobs' button.",
        f"Verify that search results are shown and at least one result lists '{location}' (case-insensitive) as the job location.",
        "Assert that the URL contains a query string with the location.",
        "If no results, verify a 'no jobs found' message is displayed."
    ]
    return {"task_type": "chronicle_location_search", "location": location, "steps": steps}

def chronicle_category_browse(_: dict) -> dict:
    category = random.choice(CATEGORIES)
    steps = [
        "Go to url 'https://jobs.chronicle.com'.",
        *_ui_hygiene(),
        "Scroll to the 'BROWSE JOBS BY POSITION TYPE' section.",
        f"Click the link for '{category}'.",
        f"Verify that the resulting page or filter shows jobs in the '{category}' category.",
        "Assert that the category name appears in the page heading or applied filters.",
        "If no jobs are found, verify a 'no jobs found' message is displayed."
    ]
    return {"task_type": "chronicle_category_browse", "category": category, "steps": steps}

def chronicle_position_type_filter(_: dict) -> dict:
    position_type = random.choice(POSITION_TYPES)
    steps = [
        "Go to url 'https://jobs.chronicle.com'.",
        *_ui_hygiene(),
        f"Click the '{position_type}' link in the main navigation or prominent section.",
        f"Verify that the resulting page lists jobs filtered by '{position_type}'.",
        "Assert that the position type appears in the page heading or applied filters.",
        "If no jobs are found, verify a 'no jobs found' message is displayed."
    ]
    return {"task_type": "chronicle_position_type_filter", "position_type": position_type, "steps": steps}

def chronicle_distance_filter(_: dict) -> dict:
    location = random.choice(LOCATIONS)
    distance = random.choice(DISTANCES)
    steps = [
        "Go to url 'https://jobs.chronicle.com'.",
        *_ui_hygiene(),
        "Locate the 'LOCATION' combobox and enter/select a location.",
        f"Set the location to '{location}'.",
        "Locate the 'WITHIN' combobox.",
        f"Select '{distance}' from the 'WITHIN' dropdown.",
        "Click the 'Find jobs' button.",
        f"Verify that search results are shown and all results are within the specified distance of '{location}' (if possible to determine).",
        "Assert that the URL contains both location and distance parameters.",
        "If no jobs are found, verify a 'no jobs found' message is displayed."
    ]
    return {"task_type": "chronicle_distance_filter", "location": location, "distance": distance, "steps": steps}

def chronicle_top_job_details(_: dict) -> dict:
    top_job = random.choice(TOP_JOB_TITLES)
    steps = [
        "Go to url 'https://jobs.chronicle.com'.",
        *_ui_hygiene(),
        "Scroll to the 'Top Jobs' section.",
        f"Click the job link with the title containing '{top_job[:32]}'.",
        f"Verify that the job details page opens and the title matches '{top_job[:32]}' (case-insensitive, partial match allowed).",
        "Assert that the job description, employer name, and location are present.",
        "Check that there is an 'Apply' or similar call-to-action button."
    ]
    return {"task_type": "chronicle_top_job_details", "top_job": top_job, "steps": steps}

def chronicle_featured_employer_browse(_: dict) -> dict:
    employer = random.choice(FEATURED_EMPLOYERS)
    steps = [
        "Go to url 'https://jobs.chronicle.com'.",
        *_ui_hygiene(),
        "Scroll to the 'Featured Employers' section.",
        f"Click the link for '{employer}'.",
        f"Verify that the employer's page or job list for '{employer}' is displayed.",
        "Assert that at least one job or employer description is visible.",
        "If no jobs are found, verify a 'no jobs found' message is displayed."
    ]
    return {"task_type": "chronicle_featured_employer_browse", "employer": employer, "steps": steps}

def chronicle_create_account_flow(_: dict) -> dict:
    fake_email = f"testuser{random.randint(10000,99999)}@example.com"
    steps = [
        "Go to url 'https://jobs.chronicle.com'.",
        *_ui_hygiene(),
        "Click the 'Create account' link in the header.",
        "Verify that the account creation form appears.",
        f"Enter a valid name and '{fake_email}' as the email address.",
        "Enter a strong password (at least 8 characters, with a number and a letter).",
        "Do not submit the form.",
        "Assert that the 'Create Account' or 'Register' button becomes enabled after filling required fields.",
        "Test form validation by leaving the email blank and verify an error is shown.",
        "Test form validation by entering an invalid email and verify an error is shown."
    ]
    return {"task_type": "chronicle_create_account_flow", "test_email": fake_email, "steps": steps}

def chronicle_job_alerts_flow(_: dict) -> dict:
    fake_email = f"alertuser{random.randint(10000,99999)}@example.com"
    steps = [
        "Go to url 'https://jobs.chronicle.com'.",
        *_ui_hygiene(),
        "Click the 'JOB ALERTS' link in the main navigation.",
        "Verify that the job alerts signup form appears.",
        f"Enter '{fake_email}' as the email address.",
        "Select at least one job category or keyword if required.",
        "Do not submit the form.",
        "Assert that the 'Create Alert' or similar button becomes enabled after filling required fields.",
        "Test form validation by leaving the email blank and verify an error is shown.",
        "Test form validation by entering an invalid email and verify an error is shown."
    ]
    return {"task_type": "chronicle_job_alerts_flow", "test_email": fake_email, "steps": steps}

def chronicle_resume_upload_flow(_: dict) -> dict:
    steps = [
        "Go to url 'https://jobs.chronicle.com'.",
        *_ui_hygiene(),
        "Locate and click the 'Upload Your Resume' link or button.",
        "Verify that the resume upload form appears.",
        "Attempt to upload a file with an invalid format (e.g., .exe) and verify an error is shown.",
        "Attempt to upload a file with a valid format (e.g., .pdf, .docx) and verify that the file is accepted (do not submit).",
        "Assert that the 'Upload' or 'Submit' button becomes enabled after a valid file is selected.",
        "Do not submit the form."
    ]
    return {"task_type": "chronicle_resume_upload_flow", "steps": steps}

def chronicle_career_resources_article(_: dict) -> dict:
    article = random.choice(CAREER_RESOURCES)
    steps = [
        "Go to url 'https://jobs.chronicle.com'.",
        *_ui_hygiene(),
        "Scroll to the 'Career Resources' section.",
        f"Click the link for '{article}'.",
        f"Verify that the article page loads and the heading matches '{article}' (case-insensitive).",
        "Assert that the article body contains at least 100 words.",
        "Check for a 'View all articles' link and verify it navigates to a list of career resources."
    ]
    return {"task_type": "chronicle_career_resources_article", "article": article, "steps": steps}

def chronicle_popular_searches(_: dict) -> dict:
    search = random.choice(POPULAR_SEARCHES)
    steps = [
        "Go to url 'https://jobs.chronicle.com'.",
        *_ui_hygiene(),
        "Scroll to the 'Popular Searches' section.",
        f"Click the link for '{search}'.",
        f"Verify that the resulting page lists jobs matching '{search}'.",
        "Assert that the search term appears in the page heading or applied filters.",
        "If no jobs are found, verify a 'no jobs found' message is displayed."
    ]
    return {"task_type": "chronicle_popular_searches", "search": search, "steps": steps}

def chronicle_employer_links(_: dict) -> dict:
    employer_link = random.choice(EMPLOYER_LINKS)
    steps = [
        "Go to url 'https://jobs.chronicle.com'.",
        *_ui_hygiene(),
        "Scroll to the 'Employer' section in the footer or navigation.",
        f"Click the '{employer_link}' link.",
        f"Verify that the correct employer page loads and the heading matches '{employer_link}' (case-insensitive, partial match allowed).",
        "Assert that the page contains relevant employer information or forms."
    ]
    return {"task_type": "chronicle_employer_links", "employer_link": employer_link, "steps": steps}

def chronicle_support_links(_: dict) -> dict:
    support_link = random.choice(SUPPORT_LINKS)
    steps = [
        "Go to url 'https://jobs.chronicle.com'.",
        *_ui_hygiene(),
        "Scroll to the 'Customer Support' section in the footer or navigation.",
        f"Click the '{support_link}' link.",
        f"Verify that the correct support page loads and the heading matches '{support_link}' (case-insensitive, partial match allowed).",
        "Assert that the page contains relevant support information or contact details."
    ]
    return {"task_type": "chronicle_support_links", "support_link": support_link, "steps": steps}

_TASK_GENERATORS: Dict[CHRONICLE_TASK_TYPES, Callable[[dict], dict]] = {
    "chronicle_keyword_search": chronicle_keyword_search,
    "chronicle_location_search": chronicle_location_search,
    "chronicle_category_browse": chronicle_category_browse,
    "chronicle_position_type_filter": chronicle_position_type_filter,
    "chronicle_distance_filter": chronicle_distance_filter,
    "chronicle_top_job_details": chronicle_top_job_details,
    "chronicle_featured_employer_browse": chronicle_featured_employer_browse,
    "chronicle_create_account_flow": chronicle_create_account_flow,
    "chronicle_job_alerts_flow": chronicle_job_alerts_flow,
    "chronicle_resume_upload_flow": chronicle_resume_upload_flow,
    "chronicle_career_resources_article": chronicle_career_resources_article,
    "chronicle_popular_searches": chronicle_popular_searches,
    "chronicle_employer_links": chronicle_employer_links,
    "chronicle_support_links": chronicle_support_links,
}

def generate_chronicle_task(task_type: CHRONICLE_TASK_TYPES, payload: dict) -> dict:
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
    items = list(CHRONICLE_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_chronicle_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)