import json, random, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

HUBSPOT_EMAILS = [
    f"testuser{i}@example.com" for i in range(1, 31)
]
HUBSPOT_SEARCH_TERMS = [
    "marketing", "sales", "automation", "CRM", "contacts", "pipeline", "lead", "deal", "email", "form",
    "workflow", "integration", "dashboard", "analytics", "report", "campaign", "blog", "SEO", "ticket", "chat",
    "calendar", "meeting", "task", "note", "company", "import", "export", "template", "sequence", "call"
]
HUBSPOT_COOKIE_ACTIONS = [
    "Accept all", "Decline all", "Manage Cookies"
]
HUBSPOT_SUPPORT_TOPICS = [
    "Cookie Policy", "Privacy Policy", "California Consumer Privacy Act (CCPA) Opt-Out", "Your Privacy Choices",
    "Account Security", "Login Issues", "Password Reset", "Data Export", "Data Deletion", "Two-Factor Authentication",
    "Integrations", "API Access", "Billing", "Subscription", "Demo Request", "Starter Plan", "Contact Support",
    "Accessibility", "Terms of Service", "Bug Report", "Feature Request"
]
HUBSPOT_YEARS = [str(y) for y in range(2005, 2026)]
HUBSPOT_DEMO_TYPES = [
    "Marketing Hub", "Sales Hub", "Service Hub", "CMS Hub", "Operations Hub", "Starter", "Professional", "Enterprise",
    "Small Business", "Startup", "Agency", "Education", "Nonprofit", "Ecommerce", "Healthcare", "Real Estate",
    "Manufacturing", "Finance", "Technology", "Consulting", "Recruitment"
]
HUBSPOT_FAKE_NAMES = [
    "Alex Smith", "Jamie Lee", "Jordan Kim", "Taylor Brown", "Morgan White", "Casey Green", "Riley Black", "Drew Gray",
    "Avery Clark", "Peyton Lewis", "Cameron Walker", "Harper Young", "Quinn Hall", "Skyler King", "Reese Wright",
    "Sawyer Scott", "Emerson Adams", "Finley Baker", "Dakota Nelson", "Rowan Carter"
]
HUBSPOT_FAKE_COMPANIES = [
    "Acme Corp", "Globex", "Initech", "Umbrella", "Wayne Enterprises", "Stark Industries", "Hooli", "Vandelay Industries",
    "Wonka Industries", "Soylent Corp", "Massive Dynamic", "Cyberdyne", "Virtucon", "Oceanic", "Pied Piper",
    "Duff Beer", "Good Burger", "Prestige Worldwide", "Monsters Inc", "Gekko & Co"
]
HUBSPOT_FAKE_PHONE = [
    f"+1-555-01{str(i).zfill(2)}-{str(j).zfill(4)}" for i in range(10, 30) for j in range(1000, 1020)
][:30]
HUBSPOT_FAKE_COUNTRIES = [
    "United States", "Canada", "United Kingdom", "Australia", "Germany", "France", "Spain", "Italy", "Netherlands",
    "Sweden", "Norway", "Denmark", "Finland", "Ireland", "New Zealand", "India", "Singapore", "Japan", "Brazil", "Mexico",
    "South Africa", "Switzerland", "Belgium", "Austria", "Portugal"
]
HUBSPOT_FAKE_PASSWORDS = [
    "Test1234!", "Password2024!", "HubSpotDemo1!", "SecurePass!2", "Qwerty!234", "DemoUser#1", "LetMeIn2024!", "MyPass!2024",
    "Hub2024!Test", "TryMe!123", "SpotHub!2024", "Demo!Pass2024", "Test!Hub2024", "Welcome!2024", "User!2024Test",
    "Hub!Spot2024", "Pass!Demo2024", "Test!User2024", "Demo!Hub2024", "Login!2024Test"
]
HUBSPOT_FAKE_EMAIL_DOMAINS = [
    "example.com", "testmail.com", "mailinator.com", "hubspotdemo.com", "fakemail.com", "mydemo.com", "demoemail.com",
    "tempmail.com", "mailhub.com", "hubmail.com", "webmail.com", "mailtest.com", "samplemail.com", "maildemo.com",
    "testhub.com", "hubspotmail.com", "mailspot.com", "mailhubspot.com", "demoaccount.com", "mailbox.com"
]
HUBSPOT_FAKE_EMAILS = [
    f"{name.lower().replace(' ','.')}@{domain}" for name, domain in zip(HUBSPOT_FAKE_NAMES, HUBSPOT_FAKE_EMAIL_DOMAINS)
]
HUBSPOT_FAKE_EMAILS = HUBSPOT_FAKE_EMAILS + HUBSPOT_EMAILS
HUBSPOT_FAKE_EMAILS = HUBSPOT_FAKE_EMAILS[:30]

HUBSPOT_FAKE_COMPANY_SIZES = [
    "1-10", "11-50", "51-200", "201-500", "501-1000", "1001-5000", "5001-10000", "10001+", "Sole Proprietor", "Startup",
    "Small Business", "Medium Business", "Large Enterprise", "Nonprofit", "Public Sector", "Freelancer", "Consultant",
    "Partnership", "LLC", "Corporation"
]

HUBSPOT_FAKE_JOB_TITLES = [
    "CEO", "CTO", "CMO", "COO", "Founder", "Manager", "Director", "VP", "Engineer", "Developer",
    "Designer", "Marketer", "Sales Rep", "Consultant", "Analyst", "Coordinator", "Specialist", "Administrator",
    "Support", "Intern"
]

HUBSPOT_FAKE_INDUSTRIES = [
    "Technology", "Finance", "Healthcare", "Education", "Retail", "Manufacturing", "Consulting", "Real Estate",
    "Ecommerce", "Nonprofit", "Media", "Travel", "Hospitality", "Construction", "Automotive", "Legal", "Energy",
    "Entertainment", "Logistics", "Telecommunications"
]

HUBSPOT_FAKE_WEBSITES = [
    f"https://www.{c.lower().replace(' ','')}.com" for c in HUBSPOT_FAKE_COMPANIES
]

HUBSPOT_FAKE_MESSAGES = [
    "Interested in learning more", "Requesting a demo", "Need help with login", "Question about pricing",
    "Looking for integration options", "Want to upgrade", "Feedback on product", "Reporting a bug",
    "Request for support", "Inquiry about features", "Need account assistance", "Interested in Starter plan",
    "Looking for training", "Want to contact sales", "Requesting callback", "Need documentation",
    "Issue with import", "Want to export data", "Looking for API info", "General inquiry"
]

HUBSPOT_FAKE_FEEDBACK = [
    "Very satisfied", "Satisfied", "Neutral", "Dissatisfied", "Very dissatisfied", "Easy to use", "Difficult to use",
    "Fast", "Slow", "Helpful", "Not helpful", "Intuitive", "Confusing", "Would recommend", "Would not recommend",
    "Great support", "Poor support", "Met expectations", "Did not meet expectations", "Excellent experience"
]

HUBSPOT_FAKE_BROWSERS = [
    "Chrome", "Firefox", "Safari", "Edge", "Opera", "Brave", "Vivaldi", "Internet Explorer", "Samsung Internet",
    "UC Browser", "Maxthon", "Puffin", "Dolphin", "Tor Browser", "Yandex", "Comodo Dragon", "Epic", "Avast Secure",
    "SRWare Iron", "Waterfox"
]

HUBSPOT_FAKE_OS = [
    "Windows 10", "Windows 11", "macOS Ventura", "macOS Monterey", "Ubuntu 22.04", "Ubuntu 20.04", "Fedora 36",
    "Debian 11", "iOS 16", "iOS 15", "Android 13", "Android 12", "Chrome OS", "Red Hat 9", "CentOS 8", "Arch Linux",
    "Windows 8.1", "macOS Big Sur", "Linux Mint", "openSUSE"
]

HUBSPOT_FAKE_SIGNUP_SOURCES = [
    "Homepage", "Blog", "Webinar", "Ad", "Referral", "Social Media", "Newsletter", "Event", "Partner", "Direct",
    "Organic Search", "Paid Search", "YouTube", "Podcast", "Customer Support", "Product Tour", "Demo", "Pricing Page",
    "Comparison Site", "Review Site"
]

HUBSPOT_TASK_TYPES = Literal[
    "hubspot_login_email",
    "hubspot_login_invalid_email",
    "hubspot_cookie_consent",
    "hubspot_get_started_free",
    "hubspot_view_cookie_policy",
    "hubspot_view_privacy_policy",
    "hubspot_classic_login_button",
    "hubspot_demo_request_link",
    "hubspot_buy_starter_link",
    "hubspot_support_topic_search"
]

HUBSPOT_SAMPLING_CONFIG: Dict[HUBSPOT_TASK_TYPES, int] = {
    "hubspot_login_email": 10,
    "hubspot_login_invalid_email": 10,
    "hubspot_cookie_consent": 10,
    "hubspot_get_started_free": 10,
    "hubspot_view_cookie_policy": 10,
    "hubspot_view_privacy_policy": 10,
    "hubspot_classic_login_button": 10,
    "hubspot_demo_request_link": 10,
    "hubspot_buy_starter_link": 10,
    "hubspot_support_topic_search": 10
}

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups or banners (e.g., cookie consent, privacy notices) if present.",
        "Do not enter any real personal information.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("HubSpot", steps).model_dump()

def hubspot_login_email(payload: dict) -> dict:
    email = random.choice(HUBSPOT_FAKE_EMAILS)
    steps = [
        "Go to url 'https://app.hubspot.com'.",
        *_ui_hygiene(),
        "Locate the textbox labeled 'Email address'.",
        f"Enter '{email}' into the email address textbox.",
        "Click the 'Next' button.",
        "Verify that the page advances to the password or authentication step, or displays an appropriate message.",
        "Do not proceed further or submit any password.",
    ]
    return {
        "task_type": "hubspot_login_email",
        "input_email": email,
        "steps": steps,
        "assertion": "Page advances to next step or shows a valid email message."
    }

def hubspot_login_invalid_email(payload: dict) -> dict:
    bad_email = random.choice([
        "notanemail", "user@.com", "@example.com", "test@", "user@invalid", "user@@example.com", "userexample.com",
        "test@com", "test@.invalid", "test@invalid.", "test@.com.", "user@-example.com", "user@exam_ple.com",
        "user@.com.com", "user@.example.com", "user@site..com", "user@.site.com", "user@site.c", "user@site.toolongtld",
        "user@site,com", "user@site;com", "user@site com", "user@site#com", "user@site@com", "user@site!com"
    ])
    steps = [
        "Go to url 'https://app.hubspot.com'.",
        *_ui_hygiene(),
        "Locate the textbox labeled 'Email address'.",
        f"Enter '{bad_email}' into the email address textbox.",
        "Click the 'Next' button.",
        "Verify that an error message appears indicating the email is invalid.",
    ]
    return {
        "task_type": "hubspot_login_invalid_email",
        "input_email": bad_email,
        "steps": steps,
        "assertion": "Error message for invalid email is displayed."
    }

def hubspot_cookie_consent(payload: dict) -> dict:
    action = random.choice(HUBSPOT_COOKIE_ACTIONS)
    steps = [
        "Go to url 'https://app.hubspot.com'.",
        "Wait for the cookie consent banner to appear.",
        f"Click the '{action}' button in the cookie consent banner.",
        "Verify that the banner disappears or updates to reflect the selection.",
    ]
    return {
        "task_type": "hubspot_cookie_consent",
        "action": action,
        "steps": steps,
        "assertion": f"Cookie banner is dismissed or reflects '{action}' selection."
    }

def hubspot_get_started_free(payload: dict) -> dict:
    name = random.choice(HUBSPOT_FAKE_NAMES)
    email = random.choice(HUBSPOT_FAKE_EMAILS)
    company = random.choice(HUBSPOT_FAKE_COMPANIES)
    phone = random.choice(HUBSPOT_FAKE_PHONE)
    country = random.choice(HUBSPOT_FAKE_COUNTRIES)
    steps = [
        "Go to url 'https://app.hubspot.com'.",
        *_ui_hygiene(),
        "Locate and click the link labeled 'Get started free'.",
        "Wait for the sign-up form to load.",
        f"Enter '{name}' for name, '{email}' for email, '{company}' for company, '{phone}' for phone, and select '{country}' as country.",
        "Submit the form.",
        "Verify that a confirmation page or message appears (e.g., 'Check your email' or 'Account created').",
        "Do not proceed with email verification or further steps.",
    ]
    return {
        "task_type": "hubspot_get_started_free",
        "input_name": name,
        "input_email": email,
        "input_company": company,
        "input_phone": phone,
        "input_country": country,
        "steps": steps,
        "assertion": "Confirmation or next-step message is displayed after form submission."
    }

def hubspot_view_cookie_policy(payload: dict) -> dict:
    steps = [
        "Go to url 'https://app.hubspot.com'.",
        *_ui_hygiene(),
        "Locate and click the link labeled 'Cookie Policy'.",
        "Verify that a new page or tab opens with information about cookies.",
        "Check that the page contains the text 'Cookie Policy' or similar.",
    ]
    return {
        "task_type": "hubspot_view_cookie_policy",
        "steps": steps,
        "assertion": "Cookie Policy page opens and contains expected content."
    }

def hubspot_view_privacy_policy(payload: dict) -> dict:
    steps = [
        "Go to url 'https://app.hubspot.com'.",
        *_ui_hygiene(),
        "Scroll to the bottom of the page.",
        "Locate and click the link labeled 'Privacy Policy'.",
        "Verify that a new page or tab opens with privacy policy information.",
        "Check that the page contains the text 'Privacy Policy' or similar.",
    ]
    return {
        "task_type": "hubspot_view_privacy_policy",
        "steps": steps,
        "assertion": "Privacy Policy page opens and contains expected content."
    }

def hubspot_classic_login_button(payload: dict) -> dict:
    steps = [
        "Go to url 'https://app.hubspot.com'.",
        *_ui_hygiene(),
        "Locate and click the button labeled 'classic login'.",
        "Verify that the classic login form or page appears.",
        "Check that the page contains fields for email and password.",
    ]
    return {
        "task_type": "hubspot_classic_login_button",
        "steps": steps,
        "assertion": "Classic login form is displayed with email and password fields."
    }

def hubspot_demo_request_link(payload: dict) -> dict:
    demo_type = random.choice(HUBSPOT_DEMO_TYPES)
    name = random.choice(HUBSPOT_FAKE_NAMES)
    email = random.choice(HUBSPOT_FAKE_EMAILS)
    company = random.choice(HUBSPOT_FAKE_COMPANIES)
    steps = [
        "Go to url 'https://app.hubspot.com'.",
        *_ui_hygiene(),
        "Locate and click the link labeled 'Get a demo'.",
        "Wait for the demo request form to load.",
        f"Select '{demo_type}' as the demo type if prompted.",
        f"Enter '{name}' for name, '{email}' for email, '{company}' for company.",
        "Submit the form.",
        "Verify that a confirmation or thank you message appears.",
    ]
    return {
        "task_type": "hubspot_demo_request_link",
        "demo_type": demo_type,
        "input_name": name,
        "input_email": email,
        "input_company": company,
        "steps": steps,
        "assertion": "Demo request confirmation or thank you message is displayed."
    }

def hubspot_buy_starter_link(payload: dict) -> dict:
    steps = [
        "Go to url 'https://app.hubspot.com'.",
        *_ui_hygiene(),
        "Locate and click the link labeled 'Buy Starter'.",
        "Verify that the page navigates to a pricing or purchase page.",
        "Check that the page contains pricing information for the Starter plan.",
        "Do not proceed with any purchase or payment.",
    ]
    return {
        "task_type": "hubspot_buy_starter_link",
        "steps": steps,
        "assertion": "Starter plan pricing page is displayed."
    }

def hubspot_support_topic_search(payload: dict) -> dict:
    topic = random.choice(HUBSPOT_SUPPORT_TOPICS)
    steps = [
        "Go to url 'https://app.hubspot.com'.",
        *_ui_hygiene(),
        f"Locate a support/help link or search box.",
        f"Search for '{topic}' in the support/help section.",
        f"Verify that results or information related to '{topic}' are displayed.",
    ]
    return {
        "task_type": "hubspot_support_topic_search",
        "support_topic": topic,
        "steps": steps,
        "assertion": f"Support/help results for '{topic}' are shown."
    }

_TASK_GENERATORS: Dict[HUBSPOT_TASK_TYPES, Callable[[dict], dict]] = {
    "hubspot_login_email": hubspot_login_email,
    "hubspot_login_invalid_email": hubspot_login_invalid_email,
    "hubspot_cookie_consent": hubspot_cookie_consent,
    "hubspot_get_started_free": hubspot_get_started_free,
    "hubspot_view_cookie_policy": hubspot_view_cookie_policy,
    "hubspot_view_privacy_policy": hubspot_view_privacy_policy,
    "hubspot_classic_login_button": hubspot_classic_login_button,
    "hubspot_demo_request_link": hubspot_demo_request_link,
    "hubspot_buy_starter_link": hubspot_buy_starter_link,
    "hubspot_support_topic_search": hubspot_support_topic_search
}

def generate_hubspot_task(task_type: HUBSPOT_TASK_TYPES, payload: dict) -> dict:
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
    items = list(HUBSPOT_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_hubspot_task, ttype, p))
                i += 1
        for fut in tqdm(as_completed(futures), total=len(futures)):
            try: out.append(fut.result(timeout=timeout))
            except Exception: pass
    with open(filepath, "w") as f:
        json.dump(out, f, indent=indent)

if __name__ == "__main__":
    fire.Fire(main)