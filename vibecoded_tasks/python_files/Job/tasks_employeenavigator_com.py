import json
import random
import datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

EMP_NAV_TASK_TYPES = Literal[
    "navigate_main_product",
    "explore_feature_learn_more",
    "request_demo",
    "newsletter_signup",
    "footer_navigation",
    "contact_company",
    "play_announcement_video",
    "explore_integrations",
    "explore_hr_management",
    "explore_benefits_admin",
    "explore_pricing",
    "explore_marketplace",
]

EMP_NAV_SAMPLING_CONFIG: Dict[EMP_NAV_TASK_TYPES, int] = {
    "navigate_main_product": 10,
    "explore_feature_learn_more": 10,
    "request_demo": 10,
    "newsletter_signup": 10,
    "footer_navigation": 10,
    "contact_company": 10,
    "play_announcement_video": 10,
    "explore_integrations": 10,
    "explore_hr_management": 10,
    "explore_benefits_admin": 10,
    "explore_pricing": 10,
    "explore_marketplace": 10,
}

# 20+ choices for variable selectors
PRODUCTS = [
    "Benefits Administration",
    "Integrations",
    "ACA Reporting",
    "Integrated Payroll",
    "New Hire Onboarding",
    "HR Management",
    "PTO Tracking",
    "Support Partners",
    "Customer Stories",
    "Blog",
    "Security",
    "Press",
    "Pricing",
    "About Us",
    "Leadership",
    "Careers",
    "Contact Us",
    "Marketplace",
    "BOOK A DEMO",
    "Login",
    "Company",
    "Resources",
    "Newsletter",
    "Facebook",
    "Twitter",
    "Vimeo",
    "LinkedIn",
]

FEATURES_LEARN_MORE = [
    "AI Technology Acquisition",
    "Benefits Administration",
    "Integrations",
    "ACA Reporting",
    "Integrated Payroll",
    "New Hire Onboarding",
    "HR Management",
    "PTO Tracking",
    "Support Partners",
    "Security",
    "Customer Stories",
    "Blog",
    "Press",
    "Pricing",
    "About Us",
    "Leadership",
    "Careers",
    "Contact Us",
    "Marketplace",
    "Newsletter",
]

FOOTER_LINKS = [
    "Benefits Administration",
    "Integrations",
    "ACA Reporting",
    "Integrated Payroll",
    "New Hire Onboarding",
    "HR Management",
    "PTO Tracking",
    "Customer Stories",
    "Blog",
    "Security",
    "Press",
    "Pricing",
    "About Us",
    "Leadership",
    "Careers",
    "Contact Us",
    "Facebook",
    "Twitter",
    "Vimeo",
    "LinkedIn",
]

CONTACT_METHODS = [
    {"type": "phone", "label": "301 - 583 - 5180"},
    {"type": "email", "label": "sales@employeenavigator.com"},
    {"type": "facebook", "label": " Facebook"},
    {"type": "twitter", "label": " Twitter"},
    {"type": "vimeo", "label": " Vimeo"},
    {"type": "linkedin", "label": " LinkedIn"},
]

INTEGRATIONS_LIST = [
    "ADP",
    "Paychex",
    "Gusto",
    "Zenefits",
    "BambooHR",
    "Namely",
    "TriNet",
    "Justworks",
    "Rippling",
    "QuickBooks Payroll",
    "Insperity",
    "Workday",
    "SAP SuccessFactors",
    "Ultimate Software",
    "Ceridian",
    "Paylocity",
    "Paycom",
    "UKG",
    "Oracle HCM",
    "BenefitMall",
    "Ease",
    "PlanSource",
    "Guardian",
    "MetLife",
    "Principal",
]

HR_FEATURES = [
    "Employee Self-Service",
    "Document Management",
    "Reporting",
    "Org Chart",
    "Class Structure",
    "Compliance Tracking",
    "Time Off Tracking",
    "HR Filing Cabinets",
    "Onboarding",
    "Integrations",
    "ACA Reporting",
    "Payroll Integration",
    "Benefits Administration",
    "PTO Tracking",
    "Support Partners",
    "Security",
    "Employee Directory",
    "Workflow Automation",
    "Notifications",
    "HR Analytics",
    "Mobile Access",
    "Role-Based Access",
]

BENEFITS_FEATURES = [
    "Open Enrollment",
    "Carrier Integrations",
    "Eligibility Management",
    "Life Event Changes",
    "COBRA Administration",
    "FSA/HSA Support",
    "Dependent Verification",
    "Employee Self-Service",
    "Reporting",
    "ACA Compliance",
    "Payroll Sync",
    "Plan Comparison",
    "Mobile Enrollment",
    "Document Library",
    "E-signatures",
    "Broker Tools",
    "Automated Reminders",
    "Audit Trails",
    "Custom Branding",
    "Data Exports",
    "Employee Communications",
    "Support Partners",
]

PRICING_FILTERS = [
    "Small Business",
    "Mid-Market",
    "Enterprise",
    "Broker",
    "Employer",
    "HR Professional",
    "Payroll Provider",
    "Insurance Carrier",
    "Integration Partner",
    "Monthly Billing",
    "Annual Billing",
    "Free Trial",
    "No Setup Fee",
    "Volume Discount",
    "Custom Quote",
    "Per Employee",
    "Per Company",
    "Add-ons",
    "Premium Support",
    "API Access",
    "Partner Pricing",
]

MARKETPLACE_CATEGORIES = [
    "Payroll",
    "HRIS",
    "Benefits",
    "Compliance",
    "Time Tracking",
    "COBRA",
    "FSA/HSA",
    "Carrier",
    "Broker Tools",
    "Employee Engagement",
    "Wellness",
    "Learning Management",
    "Performance",
    "Recruiting",
    "Background Checks",
    "Onboarding",
    "E-signature",
    "Mobile Apps",
    "Analytics",
    "Support",
    "Security",
    "Integrations",
]

def _rand_email() -> str:
    names = [
        "alex", "sam", "jordan", "casey", "taylor", "morgan", "drew", "jamie", "chris", "pat",
        "lee", "devon", "jessie", "blake", "ash", "kyle", "dana", "robin", "skyler", "quinn"
    ]
    domains = [
        "example.com", "mailinator.com", "testmail.com", "sample.org", "demo.net",
        "fakemail.com", "tempmail.com", "myemail.com", "company.com", "business.org",
        "sandbox.com", "test.org", "demo.co", "tryme.com", "nowhere.com", "mail.com",
        "inbox.com", "user.org", "workspace.com", "team.com"
    ]
    return f"{random.choice(names)}{random.randint(10,99)}@{random.choice(domains)}"

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups or banners (e.g., cookie consent, newsletter modal) if present.",
        "Do not submit any sensitive or real personal information.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Employee Navigator", steps).model_dump()

def navigate_main_product(_: dict) -> dict:
    product = random.choice(PRODUCTS)
    steps = [
        "Go to url 'https://www.employeenavigator.com'.",
        *_ui_hygiene(),
        f"Locate the main navigation bar.",
        f"Click the '{product}' link in the main navigation.",
        "Wait for the page to load or the section to expand (if applicable).",
        f"Verify that the page or section for '{product}' is displayed.",
    ]
    return {
        "task_type": "navigate_main_product",
        "product": product,
        "steps": steps,
        "assertion": f"Page or section for '{product}' is visible and URL or heading matches '{product}'."
    }

def explore_feature_learn_more(_: dict) -> dict:
    feature = random.choice(FEATURES_LEARN_MORE)
    steps = [
        "Go to url 'https://www.employeenavigator.com'.",
        *_ui_hygiene(),
        f"Scroll to the section describing '{feature}'.",
        "Locate the 'Learn More' link or button associated with this feature.",
        "Click the 'Learn More' link.",
        "Wait for the new page or expanded section to load.",
        f"Verify that additional information about '{feature}' is visible.",
    ]
    return {
        "task_type": "explore_feature_learn_more",
        "feature": feature,
        "steps": steps,
        "assertion": f"Expanded content or new page for '{feature}' is shown with relevant details."
    }

def request_demo(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.employeenavigator.com'.",
        *_ui_hygiene(),
        "Locate the 'BOOK A DEMO' button in the main navigation or page body.",
        "Click the 'BOOK A DEMO' button.",
        "Wait for the demo request form to appear.",
        "Verify that the form contains fields for name, company, email, and phone (if present).",
        "Do not submit the form.",
    ]
    return {
        "task_type": "request_demo",
        "steps": steps,
        "assertion": "Demo request form is visible with required fields (name, company, email, phone)."
    }

def newsletter_signup(_: dict) -> dict:
    email = _rand_email()
    steps = [
        "Go to url 'https://www.employeenavigator.com'.",
        *_ui_hygiene(),
        "Scroll to the footer section.",
        "Locate the newsletter signup textbox labeled 'email@address.com'.",
        f"Enter '{email}' into the textbox.",
        "Click the 'Sign up for Newsletter' button.",
        "If a reCAPTCHA appears, do not attempt to solve it.",
        "Verify that a confirmation message or banner appears (e.g., 'Thank you for subscribing').",
    ]
    return {
        "task_type": "newsletter_signup",
        "email": email,
        "steps": steps,
        "assertion": "Newsletter signup confirmation is shown or a success banner appears (without solving reCAPTCHA)."
    }

def footer_navigation(_: dict) -> dict:
    link = random.choice(FOOTER_LINKS)
    steps = [
        "Go to url 'https://www.employeenavigator.com'.",
        *_ui_hygiene(),
        "Scroll to the footer section.",
        f"Locate and click the '{link}' link in the footer.",
        "Wait for the page to load.",
        f"Verify that the '{link}' page or section is displayed.",
    ]
    return {
        "task_type": "footer_navigation",
        "footer_link": link,
        "steps": steps,
        "assertion": f"Page or section for '{link}' is visible and URL or heading matches '{link}'."
    }

def contact_company(_: dict) -> dict:
    method = random.choice(CONTACT_METHODS)
    steps = [
        "Go to url 'https://www.employeenavigator.com'.",
        *_ui_hygiene(),
        "Scroll to the footer or contact section.",
        f"Locate the contact method: '{method['label']}'.",
        f"Click the '{method['label']}' link or button.",
        "If phone: verify that a tel: link is present.",
        "If email: verify that a mailto: link is present.",
        "If social: verify that the correct social media page opens in a new tab.",
    ]
    return {
        "task_type": "contact_company",
        "contact_method": method,
        "steps": steps,
        "assertion": f"Clicking '{method['label']}' opens the correct contact method (tel/mailto/social link)."
    }

def play_announcement_video(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.employeenavigator.com'.",
        *_ui_hygiene(),
        "Locate the announcement or feature section with a 'Play' button (icon may look like '').",
        "Click the 'Play' button.",
        "Verify that a video or audio player appears and begins playback.",
        "Pause or stop the video after confirming playback.",
    ]
    return {
        "task_type": "play_announcement_video",
        "steps": steps,
        "assertion": "Video or audio player appears and playback starts after clicking 'Play'."
    }

def explore_integrations(_: dict) -> dict:
    integration = random.choice(INTEGRATIONS_LIST)
    steps = [
        "Go to url 'https://www.employeenavigator.com'.",
        *_ui_hygiene(),
        "Locate and click the 'Integrations' link in the main navigation or feature section.",
        "Wait for the integrations overview page to load.",
        f"Search for or scroll to the integration partner '{integration}'.",
        f"Verify that '{integration}' is listed as an available integration.",
    ]
    return {
        "task_type": "explore_integrations",
        "integration": integration,
        "steps": steps,
        "assertion": f"Integration partner '{integration}' is visible in the integrations list."
    }

def explore_hr_management(_: dict) -> dict:
    feature = random.choice(HR_FEATURES)
    steps = [
        "Go to url 'https://www.employeenavigator.com'.",
        *_ui_hygiene(),
        "Locate and click the 'HR Management' link in the main navigation or feature section.",
        "Wait for the HR Management page to load.",
        f"Scroll to or search for the feature '{feature}'.",
        f"Verify that information about '{feature}' is present on the page.",
    ]
    return {
        "task_type": "explore_hr_management",
        "hr_feature": feature,
        "steps": steps,
        "assertion": f"Feature '{feature}' is described or mentioned on the HR Management page."
    }

def explore_benefits_admin(_: dict) -> dict:
    feature = random.choice(BENEFITS_FEATURES)
    steps = [
        "Go to url 'https://www.employeenavigator.com'.",
        *_ui_hygiene(),
        "Locate and click the 'Benefits Administration' link in the main navigation or feature section.",
        "Wait for the Benefits Administration page to load.",
        f"Scroll to or search for the feature '{feature}'.",
        f"Verify that information about '{feature}' is present on the page.",
    ]
    return {
        "task_type": "explore_benefits_admin",
        "benefits_feature": feature,
        "steps": steps,
        "assertion": f"Feature '{feature}' is described or mentioned on the Benefits Administration page."
    }

def explore_pricing(_: dict) -> dict:
    filter_option = random.choice(PRICING_FILTERS)
    steps = [
        "Go to url 'https://www.employeenavigator.com'.",
        *_ui_hygiene(),
        "Locate and click the 'Pricing' link in the main navigation or footer.",
        "Wait for the Pricing page to load.",
        f"Look for pricing options or filters and select '{filter_option}' if available.",
        f"Verify that pricing information for '{filter_option}' is displayed or filter is applied.",
    ]
    return {
        "task_type": "explore_pricing",
        "pricing_filter": filter_option,
        "steps": steps,
        "assertion": f"Pricing for '{filter_option}' is visible or filter is applied on the Pricing page."
    }

def explore_marketplace(_: dict) -> dict:
    category = random.choice(MARKETPLACE_CATEGORIES)
    steps = [
        "Go to url 'https://www.employeenavigator.com'.",
        *_ui_hygiene(),
        "Locate and click the 'Marketplace' link in the main navigation or footer.",
        "Wait for the Marketplace page to load.",
        f"Find and select the category '{category}'.",
        f"Verify that marketplace listings or integrations for '{category}' are displayed.",
    ]
    return {
        "task_type": "explore_marketplace",
        "marketplace_category": category,
        "steps": steps,
        "assertion": f"Marketplace category '{category}' is shown with relevant listings or integrations."
    }

_TASK_GENERATORS: Dict[EMP_NAV_TASK_TYPES, Callable[[dict], dict]] = {
    "navigate_main_product": navigate_main_product,
    "explore_feature_learn_more": explore_feature_learn_more,
    "request_demo": request_demo,
    "newsletter_signup": newsletter_signup,
    "footer_navigation": footer_navigation,
    "contact_company": contact_company,
    "play_announcement_video": play_announcement_video,
    "explore_integrations": explore_integrations,
    "explore_hr_management": explore_hr_management,
    "explore_benefits_admin": explore_benefits_admin,
    "explore_pricing": explore_pricing,
    "explore_marketplace": explore_marketplace,
}

def generate_empnav_task(task_type: EMP_NAV_TASK_TYPES, payload: dict) -> dict:
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
    items = list(EMP_NAV_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_empnav_task, ttype, p))
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