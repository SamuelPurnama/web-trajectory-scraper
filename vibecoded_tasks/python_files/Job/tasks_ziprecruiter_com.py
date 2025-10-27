import json
import random
import datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

ZIP_TASK_TYPES = Literal[
    "zip_job_search",
    "zip_job_search_with_filter",
    "zip_browse_jobs_by_category",
    "zip_salary_search",
    "zip_create_account",
    "zip_employer_post_job",
    "zip_access_career_advice",
    "zip_access_support",
    "zip_view_company_info",
    "zip_access_privacy_settings",
    "zip_try_mobile_app_page",
]

ZIP_SAMPLING_CONFIG: Dict[ZIP_TASK_TYPES, int] = {
    "zip_job_search": 10,
    "zip_job_search_with_filter": 10,
    "zip_browse_jobs_by_category": 10,
    "zip_salary_search": 10,
    "zip_create_account": 10,
    "zip_employer_post_job": 10,
    "zip_access_career_advice": 10,
    "zip_access_support": 10,
    "zip_view_company_info": 10,
    "zip_access_privacy_settings": 10,
    "zip_try_mobile_app_page": 10,
}

ZIP_JOB_TITLES = [
    "Software Engineer", "Project Manager", "Registered Nurse", "Sales Associate", "Data Analyst",
    "Marketing Manager", "Customer Service Representative", "Accountant", "Administrative Assistant",
    "Business Analyst", "Graphic Designer", "Operations Manager", "Human Resources Specialist",
    "Financial Analyst", "Product Manager", "Web Developer", "Medical Assistant", "Electrician",
    "Truck Driver", "Pharmacy Technician", "Construction Laborer", "Teacher", "Executive Assistant",
    "Receptionist", "Warehouse Worker"
]

ZIP_LOCATIONS = [
    "New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX", "Phoenix, AZ",
    "Philadelphia, PA", "San Antonio, TX", "San Diego, CA", "Dallas, TX", "San Jose, CA",
    "Austin, TX", "Jacksonville, FL", "Fort Worth, TX", "Columbus, OH", "Charlotte, NC",
    "San Francisco, CA", "Indianapolis, IN", "Seattle, WA", "Denver, CO", "Washington, DC",
    "Boston, MA", "Nashville, TN", "El Paso, TX", "Detroit, MI", "Portland, OR"
]

ZIP_JOB_CATEGORIES = [
    "Healthcare", "Technology", "Sales", "Education", "Finance", "Retail", "Transportation",
    "Construction", "Hospitality", "Customer Service", "Manufacturing", "Marketing", "Legal",
    "Engineering", "Administrative", "Food Service", "Real Estate", "Government", "Science",
    "Arts", "Non-Profit", "Media", "Security", "Logistics", "Insurance"
]

ZIP_SALARY_TERMS = [
    "Software Engineer", "Registered Nurse", "Project Manager", "Accountant", "Data Analyst",
    "Marketing Manager", "Customer Service Representative", "Business Analyst", "Web Developer",
    "Product Manager", "Operations Manager", "Financial Analyst", "Medical Assistant",
    "Electrician", "Truck Driver", "Pharmacy Technician", "Construction Laborer", "Teacher",
    "Executive Assistant", "Receptionist", "Warehouse Worker", "Sales Associate", "HR Specialist",
    "Graphic Designer", "Administrative Assistant"
]

ZIP_COMPANY_SECTIONS = [
    ("About Us", "about-us"),
    ("Careers", "careers"),
    ("Investors", "investors"),
    ("Blog", "blog"),
    ("Press", "press"),
    ("Engineering", "engineering"),
    ("ZipRecruiter.org", "ziprecruiter-org"),
    ("ZipRecruiter UK", "ziprecruiter-uk")
]

ZIP_CAREER_ADVICE_TOPICS = [
    "Resume Writing", "Interview Tips", "Job Search Strategies", "Career Change", "Networking",
    "Salary Negotiation", "Remote Work", "Work-Life Balance", "Cover Letters", "Job Offer Evaluation",
    "Career Growth", "Personal Branding", "Soft Skills", "Time Management", "LinkedIn Tips",
    "Freelancing", "Dealing with Rejection", "First Job Advice", "Leadership Skills", "Upskilling",
    "Job Market Trends", "Diversity and Inclusion", "Returning to Work", "Professional Certifications", "Mentorship"
]

ZIP_SUPPORT_TOPICS = [
    "Job Seeker Support", "Employer Support", "Account Issues", "Password Reset", "Application Status",
    "Resume Upload", "Profile Editing", "Notification Settings", "Mobile App Help", "Privacy Concerns",
    "Subscription Questions", "Billing Issues", "Job Posting Help", "Fraud Reporting", "Accessibility",
    "Trust and Safety", "Contact Support", "Live Chat", "Phone Support", "Email Support", "FAQ"
]

ZIP_PRIVACY_OPTIONS = [
    "Your Privacy Choices", "Privacy Policy", "California Privacy Notice", "Terms of Use",
    "Cookie Policy", "Job Posting Rules", "Attribution Notices", "Corporate Responsibility",
    "Security and Compliance", "Read more about Ziprecruiter's Privacy Policy",
    "Read about California Privacy Notice", "Read more about Ziprecruiter's Terms of Use",
    "Read more about Ziprecruiter's Cookie Policy", "Read more about Ziprecruiter's Job Posting Rules",
    "Read more about Ziprecruiter's Attribution Notices", "Read more about Ziprecruiter's Corporate Responsibility",
    "Read more about Ziprecruiter Security and Compliance", "COVID-19 Resources", "Trust and Safety",
    "Accessibility Feedback"
]

ZIP_MOBILE_APP_FEATURES = [
    "Job Alerts", "Apply with 1 Tap", "Saved Jobs", "Application Tracking", "Push Notifications",
    "Profile Management", "Resume Upload", "Salary Search", "Job Recommendations", "Mobile Resume Builder",
    "Interview Reminders", "Employer Messaging", "Location-Based Search", "Dark Mode", "Account Settings",
    "App Security", "Privacy Controls", "Job Search Filters", "App Reviews", "App Updates", "Help Center"
]

ZIP_JOB_TYPE_FILTERS = [
    "Full-Time", "Part-Time", "Contract", "Temporary", "Internship", "Remote", "On-Site", "Hybrid",
    "Entry Level", "Mid Level", "Senior Level", "Manager", "Director", "Executive", "Hourly", "Salary",
    "Commission", "Flexible Schedule", "Night Shift", "Weekend", "Urgently Hiring"
]

def _rand_date(start_days=1, end_days=60) -> str:
    d0 = dt.date.today() + dt.timedelta(days=random.randint(start_days, end_days))
    return d0.strftime("%Y-%m-%d")

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups or banners (e.g., cookie notices, sign-up prompts) if present.",
        "Do not submit any personal or payment information.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("ZipRecruiter", steps).model_dump()

def zip_job_search(_: dict) -> dict:
    job = random.choice(ZIP_JOB_TITLES)
    location = random.choice(ZIP_LOCATIONS)
    steps = [
        "Go to url 'https://www.ziprecruiter.com'.",
        *_ui_hygiene(),
        "Locate the main job search widget.",
        f"Enter '{job}' in the 'Job Title or Keyword' field.",
        f"Enter '{location}' in the 'Location' field.",
        "Click the 'Search' button.",
        f"Verify that search results are shown for '{job}' in '{location}'.",
        "Check that at least one result is displayed.",
        "Assert that the first result contains either the job title or location.",
    ]
    return {
        "task_type": "zip_job_search",
        "job_title": job,
        "location": location,
        "steps": steps
    }

def zip_job_search_with_filter(_: dict) -> dict:
    job = random.choice(ZIP_JOB_TITLES)
    location = random.choice(ZIP_LOCATIONS)
    job_type = random.choice(ZIP_JOB_TYPE_FILTERS)
    steps = [
        "Go to url 'https://www.ziprecruiter.com'.",
        *_ui_hygiene(),
        "Locate the main job search widget.",
        f"Enter '{job}' in the 'Job Title or Keyword' field.",
        f"Enter '{location}' in the 'Location' field.",
        "Click the 'Search' button.",
        "Wait for results to load.",
        f"Apply the '{job_type}' filter from the available job type filters.",
        f"Verify that all visible results mention '{job_type}' or match the filter.",
        "Assert that at least one result remains after filtering.",
        "If no results, verify that a 'no jobs found' message is displayed.",
    ]
    return {
        "task_type": "zip_job_search_with_filter",
        "job_title": job,
        "location": location,
        "job_type_filter": job_type,
        "steps": steps
    }

def zip_browse_jobs_by_category(_: dict) -> dict:
    category = random.choice(ZIP_JOB_CATEGORIES)
    steps = [
        "Go to url 'https://www.ziprecruiter.com'.",
        *_ui_hygiene(),
        "Locate and click the 'Browse Jobs' link.",
        f"On the Browse Jobs page, select the '{category}' category.",
        f"Verify that the job listings are filtered for '{category}'.",
        "Check that at least one job is listed under this category.",
        "Assert that the category name appears in the page heading or filter.",
    ]
    return {
        "task_type": "zip_browse_jobs_by_category",
        "category": category,
        "steps": steps
    }

def zip_salary_search(_: dict) -> dict:
    term = random.choice(ZIP_SALARY_TERMS)
    steps = [
        "Go to url 'https://www.ziprecruiter.com'.",
        *_ui_hygiene(),
        "Locate and click the 'Search Salaries' link.",
        f"On the salary search page, enter '{term}' in the search field.",
        "Click the search/submit button.",
        f"Verify that salary information for '{term}' is displayed.",
        "Assert that the page shows an average or range of salaries.",
        "If no data is found, confirm that a 'no data' or similar message is shown.",
    ]
    return {
        "task_type": "zip_salary_search",
        "salary_term": term,
        "steps": steps
    }

def zip_create_account(_: dict) -> dict:
    fake_email = f"testuser{random.randint(1000,9999)}@example.com"
    steps = [
        "Go to url 'https://www.ziprecruiter.com'.",
        *_ui_hygiene(),
        "Locate and click the 'Create Free Account' link.",
        "On the registration page, fill in the required fields:",
        f"  - Email: '{fake_email}'",
        "  - Password: 'TestPassword123!'",
        "  - (If present) Name: 'Test User'",
        "Do NOT submit the form.",
        "Verify that the 'Continue' or 'Sign Up' button becomes enabled.",
        "Assert that no validation errors are shown for the entered data.",
        "Check that password requirements (if shown) are satisfied.",
    ]
    return {
        "task_type": "zip_create_account",
        "email": fake_email,
        "steps": steps
    }

def zip_employer_post_job(_: dict) -> dict:
    job = random.choice(ZIP_JOB_TITLES)
    steps = [
        "Go to url 'https://www.ziprecruiter.com'.",
        *_ui_hygiene(),
        "Locate and click the 'Post a Job' link.",
        "On the job posting page, fill in the following fields with sample data:",
        f"  - Job Title: '{job}'",
        "  - Company Name: 'Test Company'",
        "  - Location: 'Remote'",
        "  - Job Description: 'This is a sample job posting for testing.'",
        "Do NOT submit the job posting.",
        "Verify that the preview or next-step button becomes enabled.",
        "Assert that all required fields are marked as complete.",
        "Check for any validation errors and confirm none are present.",
    ]
    return {
        "task_type": "zip_employer_post_job",
        "job_title": job,
        "steps": steps
    }

def zip_access_career_advice(_: dict) -> dict:
    topic = random.choice(ZIP_CAREER_ADVICE_TOPICS)
    steps = [
        "Go to url 'https://www.ziprecruiter.com'.",
        *_ui_hygiene(),
        "Locate and click the 'Career Advice' link.",
        f"On the Career Advice page, search for or select the topic '{topic}'.",
        f"Verify that at least one article or resource about '{topic}' is displayed.",
        "Assert that the topic or keyword appears in the article title or summary.",
    ]
    return {
        "task_type": "zip_access_career_advice",
        "topic": topic,
        "steps": steps
    }

def zip_access_support(_: dict) -> dict:
    support_topic = random.choice(ZIP_SUPPORT_TOPICS)
    steps = [
        "Go to url 'https://www.ziprecruiter.com'.",
        *_ui_hygiene(),
        "Locate and click the 'Job Seeker Support' or 'Employer Support' link.",
        f"On the support page, search for or select the topic '{support_topic}'.",
        f"Verify that a support article or FAQ for '{support_topic}' is displayed.",
        "Assert that the support content includes the topic or a related keyword.",
    ]
    return {
        "task_type": "zip_access_support",
        "support_topic": support_topic,
        "steps": steps
    }

def zip_view_company_info(_: dict) -> dict:
    section, slug = random.choice(ZIP_COMPANY_SECTIONS)
    steps = [
        "Go to url 'https://www.ziprecruiter.com'.",
        *_ui_hygiene(),
        f"Scroll to the footer and locate the '{section}' link.",
        f"Click the '{section}' link.",
        f"Verify that the '{section}' page loads (URL contains '{slug}' or page heading matches).",
        f"Assert that the page contains information about '{section}'.",
    ]
    return {
        "task_type": "zip_view_company_info",
        "section": section,
        "steps": steps
    }

def zip_access_privacy_settings(_: dict) -> dict:
    privacy_opt = random.choice(ZIP_PRIVACY_OPTIONS)
    steps = [
        "Go to url 'https://www.ziprecruiter.com'.",
        *_ui_hygiene(),
        "Scroll to the footer and locate the privacy/legal links.",
        f"Click the '{privacy_opt}' link.",
        f"Verify that the corresponding privacy or legal page loads.",
        f"Assert that the page contains the title or section for '{privacy_opt}'.",
    ]
    return {
        "task_type": "zip_access_privacy_settings",
        "privacy_option": privacy_opt,
        "steps": steps
    }

def zip_try_mobile_app_page(_: dict) -> dict:
    feature = random.choice(ZIP_MOBILE_APP_FEATURES)
    steps = [
        "Go to url 'https://www.ziprecruiter.com'.",
        *_ui_hygiene(),
        "Locate and click the 'Mobile Apps' link.",
        f"On the Mobile Apps page, verify that the feature '{feature}' is mentioned or described.",
        "Assert that the feature is visible in the app description, screenshots, or FAQ.",
    ]
    return {
        "task_type": "zip_try_mobile_app_page",
        "feature": feature,
        "steps": steps
    }

_TASK_GENERATORS: Dict[ZIP_TASK_TYPES, Callable[[dict], dict]] = {
    "zip_job_search": zip_job_search,
    "zip_job_search_with_filter": zip_job_search_with_filter,
    "zip_browse_jobs_by_category": zip_browse_jobs_by_category,
    "zip_salary_search": zip_salary_search,
    "zip_create_account": zip_create_account,
    "zip_employer_post_job": zip_employer_post_job,
    "zip_access_career_advice": zip_access_career_advice,
    "zip_access_support": zip_access_support,
    "zip_view_company_info": zip_view_company_info,
    "zip_access_privacy_settings": zip_access_privacy_settings,
    "zip_try_mobile_app_page": zip_try_mobile_app_page,
}

def generate_zip_task(task_type: ZIP_TASK_TYPES, payload: dict) -> dict:
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
    items = list(ZIP_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_zip_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)