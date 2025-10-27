import json
import random
import datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, Literal
import fire
from tqdm import tqdm
from tasks.instruction_utils import get_instruction

DOTLOOP_TASK_TYPES = Literal[
    "dotloop_nav_section",
    "dotloop_plan_explore",
    "dotloop_feature_search",
    "dotloop_faq_expand",
    "dotloop_testimonial_cycle",
    "dotloop_mobile_app_info",
    "dotloop_integration_directory",
    "dotloop_resource_center",
    "dotloop_legal_policy",
    "dotloop_contact_info",
    "dotloop_trial_signup_flow",
    "dotloop_demo_request_flow",
    "dotloop_pricing_compare",
]

DOTLOOP_SAMPLING_CONFIG: Dict[DOTLOOP_TASK_TYPES, int] = {
    "dotloop_nav_section": 10,
    "dotloop_plan_explore": 10,
    "dotloop_feature_search": 10,
    "dotloop_faq_expand": 10,
    "dotloop_testimonial_cycle": 10,
    "dotloop_mobile_app_info": 10,
    "dotloop_integration_directory": 10,
    "dotloop_resource_center": 10,
    "dotloop_legal_policy": 10,
    "dotloop_contact_info": 10,
    "dotloop_trial_signup_flow": 10,
    "dotloop_demo_request_flow": 10,
    "dotloop_pricing_compare": 10,
}

# 20+ robust selectors for variable dropdowns/choices
NAV_SECTIONS = [
    "AGENTS", "BROKERS", "TEAMS", "PRICING", "RESOURCES", "TRY IT FREE", "SIGN IN", "CONTACT SALES",
    "SIGN UP FREE", "SEE PLANS", "EXPLORE PLANS", "FOR BROKERS", "FOR TEAMS", "FOR AGENTS",
    "SEE WHICH PLAN IS FOR YOU", "PLANS AND PRICING", "PREMIUM", "PRODUCTS", "BLOG", "TRAINING",
    "INTEGRATIONS", "MOBILE APP", "CUSTOMERS", "NEWSLETTER", "SUPPORT", "ABOUT US", "CAREERS"
]

PLAN_LINKS = [
    "SIGN UP FREE", "SEE PLANS", "EXPLORE PLANS", "SEE WHICH PLAN IS FOR YOU", "PLANS AND PRICING",
    "FOR BROKERS", "FOR TEAMS", "FOR AGENTS", "PREMIUM", "PRICING"
]

FEATURES = [
    "Edit real estate documents", "eSignatures for real estate", "Share documents with ease",
    "Online real estate document storage", "Compliance for real estate", "Real estate reporting",
    "Create team compliance workflows", "Build brand awareness", "Unlock transaction templates",
    "Get real-time notifications", "eSign, edit, share in one system", "Access your state and local forms",
    "Track all activity in real time", "Digitize paperwork", "Sync your CRM, back-office and more",
    "Streamline compliance", "Accelerate compliance", "Prepare and modify contracts on the go",
    "Scan documents", "Get push notifications", "Manage tasks", "Submit for review", "Forecast pending commissions",
    "Integrate with 75+ Real Estate Apps"
]

FAQ_QUESTIONS = [
    "What is transaction management software?",
    "What makes dotloop different?",
    "Can I use dotloop for free?",
    "Will dotloop help me onboard my brokerage?",
    "Is dotloop just an eSignature software?",
    "How is dotloop different from other eSignature tools?",
    "Can I access my association forms through dotloop?",
    "What are the benefits of the mobile app?",
    "Can I use dotloop even if my brokerage doesn’t?",
    "How secure is my data on dotloop?",
    "What integrations are available?",
    "How does compliance work in dotloop?",
    "What support resources are available?",
    "How do I get started?",
    "What are the pricing options?",
    "Can teams use dotloop?",
    "How do I manage documents?",
    "What mobile platforms are supported?",
    "How do I submit for review?",
    "Is there training available?",
    "How do I contact support?"
]

TESTIMONIAL_PEOPLE = [
    "Ashley Dane", "Angelique Beggins", "Jeff Cohn", "RE/MAX of Michigan", "C21 Beggins Enterprises",
    "kwELITE", "Tampa, FL", "Omaha, NE", "Metro Brokers Real Estate Services", "Keller Williams Realty",
    "Exit Realty", "Baird & Warner Real Estate", "Engel & Volkers"
]

MOBILE_APP_TOPICS = [
    "Free mobile app for real estate eSignatures",
    "Transaction management free mobile app",
    "dotloop android app download",
    "dotloop ios app download",
    "Share, edit & eSign",
    "Scan documents",
    "Get push notifications",
    "Manage tasks",
    "Submit for review",
    "Prepare and modify contracts on the go",
    "Mobile app compliance features",
    "Mobile app notifications",
    "Mobile app document scanning",
    "Mobile app task management",
    "Mobile app eSignature",
    "Mobile app templates",
    "Mobile app integrations",
    "Mobile app user reviews",
    "Mobile app onboarding",
    "Mobile app support"
]

INTEGRATION_TOPICS = [
    "CRM integrations", "Back Office integrations", "Marketing integrations", "Accounting integrations",
    "Earnnest integration", "Notarize integration", "Sync contacts", "Track ROI", "Nurture leads",
    "Measure agent performance", "Eliminate duplicate data entry", "Power marketing campaigns",
    "Forecast pending commissions", "View future business", "Get paid faster", "Accelerate Processes",
    "75+ Real Estate Apps", "Integration directory", "Third-party integrations", "API access", "Custom integrations"
]

RESOURCE_TOPICS = [
    "training options", "FREE RESOURCES", "Endless training options", "Seamless onboarding",
    "On-demand webinars", "Accredited CE courses", "Articles", "Videos", "Support resources",
    "Blog", "Resource Center", "Training", "Newsletter", "Customer stories", "Case studies",
    "Product updates", "Getting started guides", "Compliance resources", "Mobile app guides",
    "Integration guides", "FAQ"
]

LEGAL_LINKS = [
    "PRIVACY POLICY", "TERMS & CONDITIONS", "DO NOT SELL OR SHARE MY PERSONAL INFORMATION.",
    "SUPPORT", "NEWSLETTER", "ABOUT US", "CAREERS", "COMING SOON", "PRODUCTS", "BLOG",
    "RESOURCE CENTER", "TRAINING", "INTEGRATIONS", "MOBILE APP", "CUSTOMERS"
]

CONTACT_TOPICS = [
    "Contact Us", "1-888-dotloop", "support@dotloop.com", "CONTACT SALES", "SUPPORT", "NEWSLETTER",
    "AGENTS", "BROKERS", "TEAMS", "PRICING", "RESOURCES", "SIGN IN", "SIGN UP", "PREMIUM",
    "CAREERS", "ABOUT US", "CUSTOMERS", "BLOG", "TRAINING", "INTEGRATIONS"
]

TRIAL_SIGNUP_LINKS = [
    "TRY IT FREE", "SIGN UP FREE", "GET STARTED", "TRY FREE", "REQUEST A DEMO", "BUY FOR $29 USER/MONTH",
    "OR $26.16/MO BILLED ANNUALLY", "REQUEST PRICING", "SEE IT IN ACTION", "GET MORE INFO"
]

PRICING_PLANS = [
    "AGENTS", "BROKERS", "TEAMS", "PREMIUM", "PRICING", "PLANS AND PRICING", "SEE PLANS",
    "SIGN UP FREE", "BUY FOR $29 USER/MONTH", "OR $26.16/MO BILLED ANNUALLY", "REQUEST PRICING",
    "SEE WHICH PLAN IS FOR YOU", "EXPLORE PLANS", "FOR BROKERS", "FOR TEAMS", "FOR AGENTS",
    "COMPARE PLANS", "ANNUAL BILLING", "MONTHLY BILLING", "FREE TRIAL", "UPGRADE OPTIONS"
]

def _ui_hygiene() -> list[str]:
    return [
        "Dismiss any popups or banners (e.g., cookie consent, newsletter, or trial offers) if present.",
        "Do not enter any personal or payment information.",
    ]

def _instr(steps: list[str]) -> dict:
    return get_instruction("Dotloop", steps).model_dump()

def dotloop_nav_section(_: dict) -> dict:
    nav = random.choice(NAV_SECTIONS)
    steps = [
        "Go to url 'https://www.dotloop.com'.",
        *_ui_hygiene(),
        f"Locate and click the '{nav}' navigation link in the main menu.",
        "Wait for the page or section to load.",
        "Verify that the page or section heading matches or contains the selected navigation label.",
    ]
    return {
        "task_type": "dotloop_nav_section",
        "nav_section": nav,
        "steps": steps,
        "assertion": f"Page or section heading contains '{nav}'."
    }

def dotloop_plan_explore(_: dict) -> dict:
    plan = random.choice(PLAN_LINKS)
    steps = [
        "Go to url 'https://www.dotloop.com'.",
        *_ui_hygiene(),
        f"Find and click the '{plan}' link or button.",
        "Wait for the plans or pricing page/section to load.",
        "Verify that plan details or pricing options are visible.",
    ]
    return {
        "task_type": "dotloop_plan_explore",
        "plan_link": plan,
        "steps": steps,
        "assertion": "Plan details or pricing options are displayed."
    }

def dotloop_feature_search(_: dict) -> dict:
    feature = random.choice(FEATURES)
    steps = [
        "Go to url 'https://www.dotloop.com'.",
        *_ui_hygiene(),
        f"Scroll or use navigation to locate the section describing '{feature}'.",
        "Verify that the feature description is present and visible.",
    ]
    return {
        "task_type": "dotloop_feature_search",
        "feature": feature,
        "steps": steps,
        "assertion": f"Feature '{feature}' is described on the page."
    }

def dotloop_faq_expand(_: dict) -> dict:
    question = random.choice(FAQ_QUESTIONS)
    steps = [
        "Go to url 'https://www.dotloop.com'.",
        *_ui_hygiene(),
        "Scroll to the FAQ or 'Popular Questions' section.",
        f"Find the FAQ question: '{question}'.",
        "Click the '+' or expand button next to the question.",
        "Verify that the answer text becomes visible.",
        "Click the '+' or expand button again to collapse.",
        "Verify that the answer text is hidden.",
    ]
    return {
        "task_type": "dotloop_faq_expand",
        "faq_question": question,
        "steps": steps,
        "assertion": f"Answer for '{question}' expands and collapses as expected."
    }

def dotloop_testimonial_cycle(_: dict) -> dict:
    person = random.choice(TESTIMONIAL_PEOPLE)
    steps = [
        "Go to url 'https://www.dotloop.com'.",
        *_ui_hygiene(),
        "Scroll to the testimonials section (with user quotes and names).",
        "Click the 'next testimonial' button repeatedly until the testimonial for the selected person is visible, or cycle through all testimonials once.",
        f"Verify that the testimonial for '{person}' is displayed.",
        "Click the 'previous testimonial' button to cycle back.",
        "Ensure testimonial content changes accordingly.",
    ]
    return {
        "task_type": "dotloop_testimonial_cycle",
        "testimonial_person": person,
        "steps": steps,
        "assertion": f"Testimonial for '{person}' is shown after cycling."
    }

def dotloop_mobile_app_info(_: dict) -> dict:
    topic = random.choice(MOBILE_APP_TOPICS)
    steps = [
        "Go to url 'https://www.dotloop.com'.",
        *_ui_hygiene(),
        "Scroll to the section about mobile apps or search for mobile app mentions.",
        f"Find information about: '{topic}'.",
        "Verify that the topic is mentioned and described.",
    ]
    return {
        "task_type": "dotloop_mobile_app_info",
        "mobile_app_topic": topic,
        "steps": steps,
        "assertion": f"Topic '{topic}' is present in the mobile app section."
    }

def dotloop_integration_directory(_: dict) -> dict:
    integration = random.choice(INTEGRATION_TOPICS)
    steps = [
        "Go to url 'https://www.dotloop.com'.",
        *_ui_hygiene(),
        "Locate and click the 'INTEGRATIONS' or 'VIEW DIRECTORY' link.",
        "Wait for the integrations directory or section to load.",
        f"Search for or scroll to the integration topic: '{integration}'.",
        "Verify that the integration or related description is visible.",
    ]
    return {
        "task_type": "dotloop_integration_directory",
        "integration_topic": integration,
        "steps": steps,
        "assertion": f"Integration topic '{integration}' is listed or described."
    }

def dotloop_resource_center(_: dict) -> dict:
    resource = random.choice(RESOURCE_TOPICS)
    steps = [
        "Go to url 'https://www.dotloop.com'.",
        *_ui_hygiene(),
        "Locate and click the 'RESOURCE CENTER' or 'FREE RESOURCES' link.",
        "Wait for the resource center page or section to load.",
        f"Search for or scroll to the resource topic: '{resource}'.",
        "Verify that the resource or related content is present.",
    ]
    return {
        "task_type": "dotloop_resource_center",
        "resource_topic": resource,
        "steps": steps,
        "assertion": f"Resource topic '{resource}' is available in the resource center."
    }

def dotloop_legal_policy(_: dict) -> dict:
    legal = random.choice(LEGAL_LINKS)
    steps = [
        "Go to url 'https://www.dotloop.com'.",
        *_ui_hygiene(),
        f"Scroll to the footer or legal section and find the link or text: '{legal}'.",
        "Click the link if available.",
        "Verify that the relevant legal or policy information is displayed.",
    ]
    return {
        "task_type": "dotloop_legal_policy",
        "legal_link": legal,
        "steps": steps,
        "assertion": f"Legal or policy page for '{legal}' is displayed."
    }

def dotloop_contact_info(_: dict) -> dict:
    contact = random.choice(CONTACT_TOPICS)
    steps = [
        "Go to url 'https://www.dotloop.com'.",
        *_ui_hygiene(),
        "Scroll to the contact or support section.",
        f"Find the contact information or link for: '{contact}'.",
        "Verify that the contact info (phone, email, or form) is visible.",
    ]
    return {
        "task_type": "dotloop_contact_info",
        "contact_topic": contact,
        "steps": steps,
        "assertion": f"Contact info for '{contact}' is present."
    }

def dotloop_trial_signup_flow(_: dict) -> dict:
    trial = random.choice(TRIAL_SIGNUP_LINKS)
    steps = [
        "Go to url 'https://www.dotloop.com'.",
        *_ui_hygiene(),
        f"Locate and click the '{trial}' link or button.",
        "Wait for the signup or trial page to load.",
        "Verify that the signup form fields (name, email, etc.) are present.",
        "Do not submit the form.",
    ]
    return {
        "task_type": "dotloop_trial_signup_flow",
        "trial_link": trial,
        "steps": steps,
        "assertion": "Signup form fields are present on the trial page."
    }

def dotloop_demo_request_flow(_: dict) -> dict:
    steps = [
        "Go to url 'https://www.dotloop.com'.",
        *_ui_hygiene(),
        "Locate and click the 'REQUEST A DEMO' link or button.",
        "Wait for the demo request form to load.",
        "Verify that the form fields (name, email, company, etc.) are present.",
        "Do not submit the form.",
    ]
    return {
        "task_type": "dotloop_demo_request_flow",
        "steps": steps,
        "assertion": "Demo request form fields are present."
    }

def dotloop_pricing_compare(_: dict) -> dict:
    plan1, plan2 = random.sample(PRICING_PLANS, 2)
    steps = [
        "Go to url 'https://www.dotloop.com'.",
        *_ui_hygiene(),
        "Locate and click the 'PLANS AND PRICING' or 'SEE PLANS' link.",
        "Wait for the pricing page to load.",
        f"Compare the features and prices of '{plan1}' and '{plan2}' plans.",
        "Verify that both plans are listed and their main differences are visible.",
    ]
    return {
        "task_type": "dotloop_pricing_compare",
        "plan_1": plan1,
        "plan_2": plan2,
        "steps": steps,
        "assertion": f"Both '{plan1}' and '{plan2}' plans are listed with features/prices."
    }

_TASK_GENERATORS: Dict[DOTLOOP_TASK_TYPES, Callable[[dict], dict]] = {
    "dotloop_nav_section": dotloop_nav_section,
    "dotloop_plan_explore": dotloop_plan_explore,
    "dotloop_feature_search": dotloop_feature_search,
    "dotloop_faq_expand": dotloop_faq_expand,
    "dotloop_testimonial_cycle": dotloop_testimonial_cycle,
    "dotloop_mobile_app_info": dotloop_mobile_app_info,
    "dotloop_integration_directory": dotloop_integration_directory,
    "dotloop_resource_center": dotloop_resource_center,
    "dotloop_legal_policy": dotloop_legal_policy,
    "dotloop_contact_info": dotloop_contact_info,
    "dotloop_trial_signup_flow": dotloop_trial_signup_flow,
    "dotloop_demo_request_flow": dotloop_demo_request_flow,
    "dotloop_pricing_compare": dotloop_pricing_compare,
}

def generate_dotloop_task(task_type: DOTLOOP_TASK_TYPES, payload: dict) -> dict:
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
    items = list(DOTLOOP_SAMPLING_CONFIG.items())
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        i = 0
        for ttype, cnt in items:
            for _ in range(cnt):
                p = payloads[i % max(1, len(payloads))] if payloads else {}
                futures.append(ex.submit(generate_dotloop_task, ttype, p))
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