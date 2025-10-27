import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

UPWORK_TASK_TYPES = Literal[
    "upwork_search_jobs",
    "upwork_search_freelancers",
    "upwork_filter_jobs_category",
    "upwork_filter_jobs_experience",
    "upwork_filter_jobs_client_history",
    "upwork_filter_jobs_budget",
    "upwork_filter_jobs_duration",
    "upwork_filter_jobs_hours",
    "upwork_browse_categories",
    "upwork_browse_project_catalog",
    "upwork_view_job_details",
    "upwork_view_freelancer_profile",
    "upwork_signup_flow",
    "upwork_login_negative",
    "upwork_help_center_navigation",
    "upwork_language_switch",
    "upwork_browse_top_skills",
]

UPWORK_SAMPLING_CONFIG: Dict[UPWORK_TASK_TYPES, int] = {
    "upwork_search_jobs": 10,
    "upwork_search_freelancers": 10,
    "upwork_filter_jobs_category": 10,
    "upwork_filter_jobs_experience": 10,
    "upwork_filter_jobs_client_history": 10,
    "upwork_filter_jobs_budget": 10,
    "upwork_filter_jobs_duration": 10,
    "upwork_filter_jobs_hours": 10,
    "upwork_browse_categories": 10,
    "upwork_browse_project_catalog": 10,
    "upwork_view_job_details": 10,
    "upwork_view_freelancer_profile": 10,
    "upwork_signup_flow": 10,
    "upwork_login_negative": 10,
    "upwork_help_center_navigation": 10,
    "upwork_language_switch": 10,
    "upwork_browse_top_skills": 10,
}

SEARCH_TERMS = [
    "python", "javascript", "graphic design", "data entry", "wordpress", "seo", "content writing", "translation",
    "video editing", "mobile app", "virtual assistant", "accounting", "customer service", "shopify", "copywriting",
    "machine learning", "web scraping", "social media", "ui ux", "react", "node.js", "illustrator", "photoshop",
    "excel", "data analysis", "project management", "marketing", "email marketing", "proofreading", "autocad", "legal"
]

FREELANCER_SEARCH_TERMS = [
    "web developer", "designer", "translator", "accountant", "virtual assistant", "project manager", "copywriter",
    "video editor", "seo expert", "data scientist", "bookkeeper", "customer support", "mobile developer", "qa tester",
    "business analyst", "content writer", "animator", "wordpress developer", "shopify expert", "illustrator",
    "voice over", "legal consultant", "marketing specialist", "email marketer", "proofreader"
]

JOB_CATEGORIES = [
    "Web, Mobile & Software Dev", "Design & Creative", "Writing", "Sales & Marketing", "Admin Support",
    "Customer Service", "Data Science & Analytics", "Engineering & Architecture", "IT & Networking",
    "Translation", "Legal", "Accounting & Consulting", "HR & Training", "Finance", "Video & Audio",
    "Photography", "Game Development", "QA & Testing", "Project Management", "Product Management",
    "Business Consulting", "Ecommerce", "Branding", "Animation", "Transcription"
]

EXPERIENCE_LEVELS = [
    "Entry Level", "Intermediate", "Expert"
]

CLIENT_HISTORY = [
    "No hires", "1-9 hires", "10+ hires", "Payment verified", "No payment verification"
]

BUDGET_RANGES = [
    "Under $50", "$50-$200", "$200-$500", "$500-$1000", "$1000-$5000", "$5000+", "Hourly", "Fixed Price",
    "Any Budget", "Less than $10/hr", "$10-$30/hr", "$30-$60/hr", "$60+/hr", "Negotiable", "Not specified",
    "$5-$10", "$10-$20", "$20-$40", "$40-$80", "$80+"
]

JOB_DURATIONS = [
    "Less than 1 month", "1 to 3 months", "3 to 6 months", "More than 6 months", "Ongoing", "Not specified",
    "Short-term", "Long-term", "As needed", "One-time project", "Recurring", "Flexible", "Fixed duration",
    "Contract", "Temporary", "Permanent", "Seasonal", "Hourly", "Full-time", "Part-time", "Project-based"
]

HOURS_PER_WEEK = [
    "Less than 10 hrs/week", "10-30 hrs/week", "More than 30 hrs/week", "Flexible", "Not specified",
    "Full-time", "Part-time", "As needed", "Fixed", "Variable", "One-time", "Recurring", "Seasonal",
    "Temporary", "Contract", "Permanent", "Project-based", "Hourly", "Weekly", "Monthly", "Negotiable"
]

PROJECT_CATEGORIES = [
    "Logo Design", "WordPress Website", "Resume Writing", "Translation", "SEO Audit", "Business Plan",
    "Social Media Posts", "Video Animation", "Mobile App UI", "Ecommerce Store", "Branding Kit",
    "Pitch Deck", "Voice Over", "Data Analysis", "Copywriting", "Email Template", "Landing Page",
    "Product Description", "Podcast Editing", "Book Cover", "Infographic", "Presentation Design",
    "Legal Contract", "Spreadsheet Automation", "Blog Article"
]

HELP_TOPICS = [
    ("Getting Started", "getting-started"),
    ("Account & Profile", "account-profile"),
    ("Proposals & Offers", "proposals-offers"),
    ("Contracts & Work", "contracts-work"),
    ("Payments & Earnings", "payments-earnings"),
    ("Disputes & Issues", "disputes-issues"),
    ("Client Support", "client-support"),
    ("Freelancer Support", "freelancer-support"),
    ("Verification", "verification"),
    ("Security", "security"),
    ("Upwork Fees", "fees"),
    ("Connects", "connects"),
    ("Messages", "messages"),
    ("Mobile App", "mobile-app"),
    ("Notifications", "notifications"),
    ("Reports", "reports"),
    ("Tax Information", "tax"),
    ("Identity", "identity"),
    ("Feedback", "feedback"),
    ("Job Success Score", "jss"),
    ("Project Catalog", "project-catalog"),
    ("Talent Scout", "talent-scout"),
    ("Enterprise", "enterprise"),
    ("Direct Contracts", "direct-contracts"),
    ("Upwork Academy", "academy")
]

LANGUAGES = [
    "English", "Deutsch", "Español", "Français", "Português", "Italiano", "Nederlands", "Polski", "Türkçe",
    "Русский", "Українська", "العربية", "中文", "日本語", "한국어", "Bahasa Indonesia", "Tiếng Việt", "ไทย",
    "Filipino", "Magyar", "Čeština"
]

TOP_SKILLS = [
    "Python", "JavaScript", "React", "Node.js", "WordPress", "Graphic Design", "SEO", "Content Writing",
    "Translation", "Data Entry", "Video Editing", "Mobile App Development", "Virtual Assistant", "Accounting",
    "Customer Service", "Shopify", "Copywriting", "Machine Learning", "Web Scraping", "Social Media Marketing",
    "UI/UX Design", "Illustrator", "Photoshop", "Excel", "Data Analysis", "Project Management", "Marketing",
    "Email Marketing", "Proofreading", "AutoCAD", "Legal Consulting"
]

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups, cookie banners, or onboarding overlays.",
        "Do not attempt to log in, sign up, or submit forms unless instructed.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Upwork", steps).model_dump()

def upwork_search_jobs(_: dict) -> dict:
    term = random.choice(SEARCH_TERMS)
    steps = [
        "Go to url 'https://www.upwork.com/' with the main search bar visible.",
        *_ui_hygiene(),
        f"Focus the main search bar and type '{term}'.",
        "Select 'Jobs' as the search type if not already selected.",
        "Submit the search.",
        "Wait for the results page to load with job listings.",
        f"Assert that at least one job result contains the term '{term}' in the title or description.",
        "Verify the URL contains '/search/jobs/' and the search term.",
    ]
    return {"task_type": "upwork_search_jobs", "search_term": term, "steps": steps}

def upwork_search_freelancers(_: dict) -> dict:
    term = random.choice(FREELANCER_SEARCH_TERMS)
    steps = [
        "Go to url 'https://www.upwork.com/' with the main search bar visible.",
        *_ui_hygiene(),
        f"Focus the main search bar and type '{term}'.",
        "Select 'Talent' as the search type.",
        "Submit the search.",
        "Wait for the results page to load with freelancer profiles.",
        f"Assert that at least one freelancer result contains the term '{term}' in the title or skills.",
        "Verify the URL contains '/search/profiles/' and the search term.",
    ]
    return {"task_type": "upwork_search_freelancers", "search_term": term, "steps": steps}

def upwork_filter_jobs_category(_: dict) -> dict:
    category = random.choice(JOB_CATEGORIES)
    steps = [
        "Go to url 'https://www.upwork.com/' with the main search bar visible.",
        *_ui_hygiene(),
        "Click the 'Find Work' or 'Find Jobs' link in the main navigation.",
        "On the jobs search page, open the 'Category' filter dropdown.",
        f"Select the category '{category}'.",
        "Apply the filter.",
        f"Assert that the first page of job results contains jobs in the '{category}' category.",
        "Verify the filter chip or sidebar shows the selected category.",
    ]
    return {"task_type": "upwork_filter_jobs_category", "category": category, "steps": steps}

def upwork_filter_jobs_experience(_: dict) -> dict:
    level = random.choice(EXPERIENCE_LEVELS)
    steps = [
        "Go to url 'https://www.upwork.com/nx/jobs/' (jobs search page).",
        *_ui_hygiene(),
        "Open the 'Experience Level' filter.",
        f"Select '{level}'.",
        "Apply the filter.",
        f"Assert that the first page of results shows jobs with experience level '{level}'.",
        "Verify the filter chip or sidebar shows the selected experience level.",
    ]
    return {"task_type": "upwork_filter_jobs_experience", "experience_level": level, "steps": steps}

def upwork_filter_jobs_client_history(_: dict) -> dict:
    history = random.choice(CLIENT_HISTORY)
    steps = [
        "Go to url 'https://www.upwork.com/nx/jobs/' (jobs search page).",
        *_ui_hygiene(),
        "Open the 'Client History' or 'Client Info' filter.",
        f"Select '{history}'.",
        "Apply the filter.",
        f"Assert that the first page of results shows jobs with client history '{history}'.",
        "Verify the filter chip or sidebar shows the selected client history.",
    ]
    return {"task_type": "upwork_filter_jobs_client_history", "client_history": history, "steps": steps}

def upwork_filter_jobs_budget(_: dict) -> dict:
    budget = random.choice(BUDGET_RANGES)
    steps = [
        "Go to url 'https://www.upwork.com/nx/jobs/' (jobs search page).",
        *_ui_hygiene(),
        "Open the 'Budget' or 'Hourly Rate' filter.",
        f"Select '{budget}'.",
        "Apply the filter.",
        f"Assert that the first page of results shows jobs with budget or hourly rate '{budget}'.",
        "Verify the filter chip or sidebar shows the selected budget/rate.",
    ]
    return {"task_type": "upwork_filter_jobs_budget", "budget_range": budget, "steps": steps}

def upwork_filter_jobs_duration(_: dict) -> dict:
    duration = random.choice(JOB_DURATIONS)
    steps = [
        "Go to url 'https://www.upwork.com/nx/jobs/' (jobs search page).",
        *_ui_hygiene(),
        "Open the 'Project Length' or 'Duration' filter.",
        f"Select '{duration}'.",
        "Apply the filter.",
        f"Assert that the first page of results shows jobs with duration '{duration}'.",
        "Verify the filter chip or sidebar shows the selected duration.",
    ]
    return {"task_type": "upwork_filter_jobs_duration", "job_duration": duration, "steps": steps}

def upwork_filter_jobs_hours(_: dict) -> dict:
    hours = random.choice(HOURS_PER_WEEK)
    steps = [
        "Go to url 'https://www.upwork.com/nx/jobs/' (jobs search page).",
        *_ui_hygiene(),
        "Open the 'Hours per week' or 'Workload' filter.",
        f"Select '{hours}'.",
        "Apply the filter.",
        f"Assert that the first page of results shows jobs with hours per week '{hours}'.",
        "Verify the filter chip or sidebar shows the selected hours per week.",
    ]
    return {"task_type": "upwork_filter_jobs_hours", "hours_per_week": hours, "steps": steps}

def upwork_browse_categories(_: dict) -> dict:
    category = random.choice(JOB_CATEGORIES)
    steps = [
        "Go to url 'https://www.upwork.com/' with the main navigation visible.",
        *_ui_hygiene(),
        "Hover or click the 'Find Talent' or 'Find Work' menu.",
        f"Select the category '{category}' from the dropdown or sidebar.",
        "Wait for the category page to load.",
        f"Assert that the page heading or breadcrumb contains '{category}'.",
        "Verify that jobs or freelancers in this category are listed.",
    ]
    return {"task_type": "upwork_browse_categories", "category": category, "steps": steps}

def upwork_browse_project_catalog(_: dict) -> dict:
    project = random.choice(PROJECT_CATEGORIES)
    steps = [
        "Go to url 'https://www.upwork.com/catalog/' (Project Catalog).",
        *_ui_hygiene(),
        f"Type '{project}' into the Project Catalog search bar.",
        "Submit the search.",
        "Wait for the results page to load.",
        f"Assert that at least one project listing contains '{project}' in the title or description.",
        "Verify the URL contains '/catalog/' and the search term.",
    ]
    return {"task_type": "upwork_browse_project_catalog", "project_category": project, "steps": steps}

def upwork_view_job_details(_: dict) -> dict:
    term = random.choice(SEARCH_TERMS)
    steps = [
        "Go to url 'https://www.upwork.com/' with the main search bar visible.",
        *_ui_hygiene(),
        f"Search for '{term}' in jobs.",
        "Wait for the results page to load.",
        "Click on the first job listing.",
        "Wait for the job details page to load.",
        "Assert that the job title, description, and client info are visible.",
        "Verify that the URL contains '/jobs/' and a job ID.",
    ]
    return {"task_type": "upwork_view_job_details", "search_term": term, "steps": steps}

def upwork_view_freelancer_profile(_: dict) -> dict:
    term = random.choice(FREELANCER_SEARCH_TERMS)
    steps = [
        "Go to url 'https://www.upwork.com/' with the main search bar visible.",
        *_ui_hygiene(),
        f"Search for '{term}' in talent.",
        "Wait for the results page to load.",
        "Click on the first freelancer profile.",
        "Wait for the profile page to load.",
        "Assert that the freelancer's name, title, and skills are visible.",
        "Verify that the URL contains '/freelancers/' and a profile ID.",
    ]
    return {"task_type": "upwork_view_freelancer_profile", "search_term": term, "steps": steps}

def upwork_signup_flow(_: dict) -> dict:
    names = ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Skyler", "Jamie", "Riley", "Avery", "Peyton",
             "Quinn", "Drew", "Harper", "Reese", "Rowan", "Sawyer", "Emerson", "Finley", "Hayden", "Jesse"]
    name = random.choice(names)
    email = f"testuser{random.randint(10000,99999)}@example.com"
    steps = [
        "Go to url 'https://www.upwork.com/signup/' (sign up page).",
        *_ui_hygiene(),
        f"Enter '{name}' as the first name.",
        f"Enter '{name}Test' as the last name.",
        f"Enter '{email}' as the email address.",
        "Enter a valid password (e.g., 'TestUser123!').",
        "Select 'Work as a Freelancer' or 'Hire for a project' at random.",
        "Accept the Terms of Service.",
        "Do not submit the form.",
        "Assert that the 'Sign Up' button becomes enabled.",
        "Verify that no error messages are shown for the entered fields.",
    ]
    return {"task_type": "upwork_signup_flow", "first_name": name, "last_name": f"{name}Test", "email": email, "steps": steps}

def upwork_login_negative(_: dict) -> dict:
    email = f"notareal{random.randint(10000,99999)}@example.com"
    steps = [
        "Go to url 'https://www.upwork.com/ab/account-security/login' (login page).",
        *_ui_hygiene(),
        f"Enter '{email}' as the email address.",
        "Enter 'WrongPassword123!' as the password.",
        "Click the 'Log In' button.",
        "Wait for the error message to appear.",
        "Assert that an error message is shown indicating invalid credentials.",
        "Verify that the user is not redirected to a dashboard or account page.",
    ]
    return {"task_type": "upwork_login_negative", "email": email, "steps": steps}

def upwork_help_center_navigation(_: dict) -> dict:
    topic, slug = random.choice(HELP_TOPICS)
    steps = [
        "Go to url 'https://support.upwork.com/hc/en-us' (Help Center).",
        *_ui_hygiene(),
        f"Search for '{topic}' in the Help Center search bar.",
        "Submit the search.",
        "Wait for the results page to load.",
        f"Click on the first article related to '{topic}'.",
        "Assert that the article page loads and the heading contains '{topic}'.",
        "Verify the URL contains the help center and the topic slug.",
    ]
    return {"task_type": "upwork_help_center_navigation", "help_topic": topic, "steps": steps}

def upwork_language_switch(_: dict) -> dict:
    lang = random.choice(LANGUAGES)
    steps = [
        "Go to url 'https://www.upwork.com/' with the footer visible.",
        *_ui_hygiene(),
        "Scroll to the footer and locate the language selector.",
        f"Select '{lang}' from the language options.",
        "Wait for the page to reload or update.",
        f"Assert that the main navigation or footer is now shown in '{lang}' (or the language code).",
        "Verify that the URL contains a language parameter or the UI text changes.",
    ]
    return {"task_type": "upwork_language_switch", "language": lang, "steps": steps}

def upwork_browse_top_skills(_: dict) -> dict:
    skill = random.choice(TOP_SKILLS)
    steps = [
        "Go to url 'https://www.upwork.com/' with the main navigation visible.",
        *_ui_hygiene(),
        "Hover or click the 'Browse' or 'Find Talent' menu.",
        "Open the 'Top Skills' or 'Browse by Skill' section.",
        f"Select the skill '{skill}'.",
        "Wait for the skill page to load.",
        f"Assert that the page heading or breadcrumb contains '{skill}'.",
        "Verify that freelancers with the skill '{skill}' are listed.",
    ]
    return {"task_type": "upwork_browse_top_skills", "skill": skill, "steps": steps}

_TASK_GENERATORS: Dict[UPWORK_TASK_TYPES, Callable[[dict], dict]] = {
    "upwork_search_jobs": upwork_search_jobs,
    "upwork_search_freelancers": upwork_search_freelancers,
    "upwork_filter_jobs_category": upwork_filter_jobs_category,
    "upwork_filter_jobs_experience": upwork_filter_jobs_experience,
    "upwork_filter_jobs_client_history": upwork_filter_jobs_client_history,
    "upwork_filter_jobs_budget": upwork_filter_jobs_budget,
    "upwork_filter_jobs_duration": upwork_filter_jobs_duration,
    "upwork_filter_jobs_hours": upwork_filter_jobs_hours,
    "upwork_browse_categories": upwork_browse_categories,
    "upwork_browse_project_catalog": upwork_browse_project_catalog,
    "upwork_view_job_details": upwork_view_job_details,
    "upwork_view_freelancer_profile": upwork_view_freelancer_profile,
    "upwork_signup_flow": upwork_signup_flow,
    "upwork_login_negative": upwork_login_negative,
    "upwork_help_center_navigation": upwork_help_center_navigation,
    "upwork_language_switch": upwork_language_switch,
    "upwork_browse_top_skills": upwork_browse_top_skills,
}

def generate_upwork_task(task_type: UPWORK_TASK_TYPES, payload: dict) -> dict:
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
    items = list(UPWORK_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_upwork_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)