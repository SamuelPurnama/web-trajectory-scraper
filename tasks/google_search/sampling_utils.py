import random
import datetime
from typing import Literal, Optional
import json
import os
import requests

import ell
from pydantic import BaseModel, Field

from tasks.instruction_utils import get_instruction

from urllib.parse import urlparse


GOOGLE_SEARCH_TASK_TYPES = [
    "google_basic_search",
    "google_title_search",
    "google_comparison",
    "google_subpage_search",
    "google_date_filter_search",
    "google_site_search",
    "google_qa",
]


def google_search(query: str, num_results: int = 10) -> dict:
    response = requests.request(
        "POST",
        "https://google.serper.dev/search",
        data=json.dumps({"q": query, "num": num_results}),
        headers = {
          'X-API-KEY': os.environ['SERPER_DEV_API_KEY'],
          'Content-Type': 'application/json'
        },
    )
    return dict(
        pages=response.json()["organic"] if response.status_code == 200 else [],
        response=response,
    )


def get_google_search_keywords_generator():
    class SearchKeywords(BaseModel):
        keywords: list[str] = Field(description="The list of search keywords")

    @ell.complex(model="gpt-4o", response_format=SearchKeywords)
    def lmp(persona: str, num_keywords: int):
        return [
            ell.system(f"You are {persona}"),
            ell.user(
                f"Generate {num_keywords} search keywords that you would use on Google Search to find information relevant to your interests."
                # + " Generate keywords that are likely to be titles of wikipedia articles."
            ),
        ]

    def get_google_search_keywords_from_llm(
        persona: str, num_keywords: int
    ) -> list[str]:
        return lmp(persona, num_keywords).parsed.keywords  # type: ignore

    return get_google_search_keywords_from_llm


def create_google_search_basic_search_task(keyword):
    steps = [
        "Unless already on a google search page with the search bar visible, go to https://www.google.com",
        "If you see a pop up to 'sign in', simply ignore it, stay signed out, and proceed to the search bar.",
        f"Click on the search bar, then search for '{keyword}' using the search input box",
    ]
    steps.append("Once you are on the results page, exit.")
    return [
        dict(
            task_type="google_basic_search",
            keyword=keyword,
            steps=steps,
        )
    ]


def create_google_subpage_search_task(keyword: str, sub_page: Literal["Images", "News", "Shopping", "Videos"]) -> list[dict]:
    """
    Search Google for `keyword`, click the given `tab` (e.g. "Images", "News", "Shopping") and return its results.
    """
    steps = [
        "Unless already on a google search page with the search bar visible, go to https://www.google.com",
        "If you see a pop up to 'sign in', simply ignore it, stay signed out.",
        f"Click on the search bar, then search for '{keyword}' using the search input box",
        f"Once you are on the results page, click on the '{sub_page}' button."
        "Click on the link to the most relavent result then exit."
    ]
    return [
        dict(
            task_type="google_subpage_search",
            keyword=keyword,
            sub_page=sub_page,
            steps=steps,
        )
    ]


def create_google_date_filter_search_task(
    keyword: str,
    filter_option: Optional[Literal[
        "Any time",
        "Past hour",
        "Past 24 hours",
        "Past week",
        "Past month",
        "Past year",
        "Custom range...",
    ]] = None,
    start_date: Optional[str] = None,  # "M/D/YYYY"
    end_date: Optional[str] = None,    # "M/D/YYYY"
) -> list[dict]:
    options = [
        "Any time",
        "Past hour",
        "Past 24 hours",
        "Past week",
        "Past month",
        "Past year",
        "Custom range...",
    ]
    if filter_option is None:
        filter_option = random.choice(options)

    steps = [
        "Unless already on a Google search page with the search bar visible, go to https://www.google.com",
        "If you see a pop-up to 'sign in', ignore it and stay signed out",
        f"Click on the search bar, then search for '{keyword}' using the search input box",
        "Once you are on the results page click on the 'Tools' button to reveal the filtering options",
        "Click on the dropdown that currently says 'Any time' to reveal the rest of the filtering options",
        f"Select '{filter_option}'.",
    ]

    if filter_option == "Custom range...":
        if start_date is None or end_date is None:
            today = datetime.date.today()
            earliest = today - datetime.timedelta(days=20 * 365)
            span = (today - earliest).days
            rand_start = earliest + datetime.timedelta(days=random.randint(0, span))

            end_span = (today - rand_start).days
            rand_end = rand_start + datetime.timedelta(days=random.randint(0, end_span))

            start_date = f"{rand_start.month}/{rand_start.day}/{rand_start.year}"
            end_date = f"{rand_end.month}/{rand_end.day}/{rand_end.year}"

        steps += [
            "Click on the 'Custom range...' option",
            f"Click the 'From' date field and type in {start_date}",
            f"Click the 'To' date field and type in {end_date}",
            "Click the 'Go' button to apply the custom date range",
        ]

    return [{
        "task_type": "google_date_filter_search",
        "keyword": keyword,
        "filter_option": filter_option,
        **({"start_date": start_date, "end_date": end_date}
           if filter_option == "Custom range..." else {}),
        "steps": steps,
    }]


def create_google_site_search_task(
    keyword: str,
    persona: str
) -> list[dict]:
    """
    Ask the persona which sites they trust for `keyword`, then search Google with 'site:$TRUSTED_SITE'.
    """
    class TrustedSites(BaseModel):
        sites: list[str] = Field(
            description=f"Domains you trust for accurate information on '{keyword}'"
        )

    @ell.complex(model="gpt-4o", response_format=TrustedSites)
    def lmp(persona: str, keyword: str):
        return [
            ell.system(f"You are {persona}"),
            ell.user(
                "For searching information about "
                f"'{keyword}', list three websites (as domains) you trust most."
                " Ensure that they are of the form SUBDOMAIN.DOMAIN_NAME.TLD, as an example www.evo.com."
            ),
        ]

    trusted = lmp(persona, keyword).parsed.sites  # type: ignore
    trusted_site = random.choice(trusted)

    steps = [
        "Unless already on a Google search page with the search bar visible, go to https://www.google.com",
        "If you see a pop-up to 'sign in', ignore it and stay signed out",
        f"Click on the search bar, then search for 'site:{trusted_site} {keyword}' using the search input box",
        "On the results page, click the most relevant link and return it to the user and exit.",
    ]

    return [{
        "task_type": "google_site_search",
        "keyword": keyword,
        "site": trusted_site,
        "steps": steps,
    }]


def create_google_qa_task(
    keyword: str,
    persona: str
) -> list[dict]:
    """
    Generate a single Q&A task: search Google for a factual question about `keyword` and find the answer.
    """
    class Question(BaseModel):
        question: str = Field(
            description=f"Factual question you'd ask Google about '{keyword}'"
        )

    @ell.complex(model="gpt-4o", response_format=Question)
    def lmp(persona: str, keyword: str):
        return [
            ell.system(f"You are {persona}"),
            ell.user(
                f"Generate one concise factual question you would search on Google about '{keyword}'"
            ),
        ]

    question = lmp(persona, keyword).parsed.question  # type: ignore

    steps = [
        "Unless already on a Google search page with the search bar visible, go to https://www.google.com",
        "If you see a pop-up to 'sign in', ignore it and stay signed out",
        f"Click on the search bar, then search for '{question}' using the search input box",
        f"On the results page, If there is an 'AI Overview' avaiable, click show more.",
        f"Scroll down until you have found the information that answers {question}",
        f"If there is no 'AI Overview' available, scroll through the results to find a page that will answer the question: '{question}'.",
        "Once you have found a page that will contain the answer, return it to the user and exit"
    ]

    return [{
        "task_type": "google_qa",
        "keyword": keyword,
        "question": question,
        "steps": steps,
    }]


def create_google_search_title_search_task(keyword: str, persona: str) -> dict:
    # Gather initial results for query
    pages = google_search(keyword)["pages"]

    # If there is nothing related to that keyword, skip it.
    if len(pages) == 0:
        return {}

    # Select a random page to create a reverse query from
    page_idx = random.randint(0, len(pages) - 1)
    selected_page = pages[page_idx]

    # Create a query that would lead to that page on google
    def get_base_url(url: str) -> str:
        return urlparse(url).netloc

    steps = [
        "Unless already on a google search page with the search bar visible, go to https://www.google.com",
        "If you see a pop up to 'sign in', simply ignore it, stay signed out, and proceed to the search bar.",
        f"Click on the search bar, then type in a search query that would bring you to the {selected_page['title']} page on {get_base_url(selected_page['link'])}",
    ]

    if len(pages) == 0:
        steps.append(
            f"This specific search will likely not produce a search result. " + \
            f"If so, let the user know there were no search results found for '${{YOUR QUERY}}' and ask the user if they would like to search with a different query."
        )
    else:
        steps.append(
            f"When you end up on the search results page, scroll down to until you find the {selected_page['title']} page on {get_base_url(selected_page['link'])}. "
        )

        steps.append(
            f"If none of the suggested pages on the first page of the results are the {selected_page['title']} page on {get_base_url(selected_page['link'])}," + \
            " scroll down to the bottom of the google search results page and click on the `Next` button to go to the next page of results."
        )
        steps.append("If you have found the page, click on the link and return it to the user, if you are unable to find the requested page, notify the user and exit.")

    return [
        dict(
            task_type="google_title_search",
            keyword=keyword,
            page=selected_page,
            steps=steps,
        )
    ]


def create_google_search_compare_task(keyword: str, persona: str) -> dict:
    class Comparison(BaseModel):
        option_1: str = Field(description=f"Something related to '{keyword}' that will be compared against")
        option_2: str = Field(description=f"Something related to '{keyword}' that will be compared against")
    @ell.complex(model="gpt-4o", response_format=Comparison)
    def lmp(persona: str):
        return [
            ell.system(f"You are {persona}"),
            ell.user(
                f"Generate a pair of things to compare that you as a consumer could purchase. "
                f"Make sure that it is specific to your interests, and that it is related to '{keyword}'. "
                f"A good example for 'tablets' would be 'Apple iPad Pro' and 'Samsung Galaxy Tab S10 Ultra'."
            ),
        ]
    options: Comparison = lmp(persona).parsed

    steps = [
        "Unless already on a google search page with the search bar visible, go to https://www.google.com",
        "If you see a pop up to 'sign in', simply ignore it, stay signed out, and proceed to the search bar.",
        f"Click on the search bar, and search for {options.option_1}.",
    ]

    steps.append(f"When you end up on the search results page, scroll down to until you find a page contraining the relevant information about using/getting '{options.option_1}'.")
    steps.append(f"Click the page containing the relavent information to {options.option_1}.")
    steps.append(f"Scroll through and read the key sections of the page noting the relative pros and cons of using/getting '{options.option_1}'")
    steps.append(f"Once you feel that you have enough information about '{options.option_1}', go back to https://www.google.com and repeat all of the previous steps, except instead search for information that pertains to {options.option_2}")

    steps.append(f"Once you have enough information about both '{options.option_1}' and '{options.option_2}' to accurately compare them, make that comparison and report it to the user.")

    return [
        dict(
            task_type="google_comparison",
            keyword=keyword,
            option_1=options.option_1,
            option_2=options.option_2,
            steps=steps,
        )
    ]


def generate_google_search_task(
    persona: str,
    task_type: Literal[
        "google_basic_search",
        "google_title_search",
        "google_comparison",
        "google_subpage_search",
        "google_date_filter_search",
        "google_site_search",
        "google_shopping",
    ],
    keyword: Optional[str] = None,
):
    if not keyword:
        keyword = get_google_search_keywords_generator()(
            persona=persona, num_keywords=1
        )[0]

    if task_type == "google_basic_search":
        task = create_google_search_basic_search_task(keyword)[0]
    elif task_type == "google_title_search":
        task = create_google_search_title_search_task(keyword, persona)[0]
    elif task_type == "google_comparison":
        task = create_google_search_compare_task(keyword, persona)[0]
    elif task_type == "google_subpage_search":
        choice = random.choice(["Images", "News", "Shopping", "Videos"])
        task = create_google_subpage_search_task(keyword, choice)[0]
    elif task_type == "google_date_filter_search":
        task = create_google_date_filter_search_task(keyword)[0]
    elif task_type == "google_site_search":
        task = create_google_site_search_task(keyword, persona)[0]
    elif task_type == "google_shopping":
        task = create_google_subpage_search_task(keyword, "Shopping")[0]
    elif task_type == "google_qa":
        task = create_google_qa_task(keyword, persona)[0]
    else:
        raise NotImplementedError(f"Unknown task_type: {task_type}")

    task["instruction"] = get_instruction("google_search", task["steps"]).model_dump()
    return task


if __name__ == '__main__':
    # persona = "A backyard grill master who loves to share tips and tricks for achieving the perfect smoky flavor"
    # persona = "A solo backpacker with a similar interest in photography, eager to capture unique perspectives"
    persona = "A retired professor in Linguistics who studied together with Celso Alvarez Caccamo"
    tasks = {}
    tasks_to_run = GOOGLE_SEARCH_TASK_TYPES
    # tasks_to_run = ["google_qa"]

    for task_type in tasks_to_run:
        tasks[task_type] = generate_google_search_task(
            persona,
            task_type,
        )
        print(f"task type: {task_type} = {tasks[task_type]}")

    import ipdb; ipdb.set_trace()

