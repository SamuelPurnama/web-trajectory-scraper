import random
from typing import Literal, Optional

import ell
from pydantic import BaseModel, Field

import tasks.wikipedia.wikipedia_api as wikipedia_api
from tasks.instruction_utils import get_instruction
from tasks.persona_utils import read_personas


def get_wikipedia_keywords_generator():
    class SearchKeywords(BaseModel):
        keywords: list[str] = Field(description="The list of search keywords")

    @ell.complex(model="gpt-4o", response_format=SearchKeywords)
    def lmp(persona: str, num_keywords: int):
        return [
            ell.system(f"You are {persona}"),
            ell.user(
                f"Generate {num_keywords} search keywords that you might use on Wikipedia to find information relevant to your interests. Generate keywords that are likely to be titles of wikipedia articles."
            ),
        ]

    def get_wikipedia_keywords_from_llm(
        persona: str, num_keywords: int
    ) -> list[str]:
        return lmp(persona, num_keywords).parsed.keywords  # type: ignore

    return get_wikipedia_keywords_from_llm


def create_wikipedia_basic_search_task(keyword):
    pages = wikipedia_api.wikipedia_search(keyword)["pages"]
    steps = [
        "Unless already on a wikipedia page with the search bar visible, go to https://en.wikipedia.org",
        f"Search for '{keyword}' using the search input box",
    ]
    if len(pages) == 0:
        steps.append(
            f"This search will likely not produce a search result. If so, let the user know there were no search results found for keyword '{keyword}' and ask the user if they would like to search with a different keyword."
        )
    else:
        steps.append(
            f"If you end up on a 'Search results' page, let the user know that you did not find an exact match but some closesly related articles. Otherwise, if you are on the article page, let the user know you have found the wikipedia article titled '{pages[0]['title']}'"
        )

    return [
        dict(
            task_type="wikipedia_basic_search",
            keyword=keyword,
            page=pages[0] if len(pages) > 0 else None,
            steps=steps,
        )
    ]


def create_wikipedia_goto_section_task(keyword: str, num_tasks: int):
    page_and_content = wikipedia_api.get_first_page_content(keyword)
    if page_and_content is None:
        return []

    page = page_and_content["page"]
    content = page_and_content["content"]
    headings = wikipedia_api.extract_headings_from_markdown(content)

    tasks = []
    for i in range(num_tasks):
        idx = random.choice(range(len(headings)))
        level = headings[idx]["level"]
        heading = headings[idx]["heading"]

        steps = [
            "Unless already on a wikipedia page with the search bar visible, go to https://en.wikipedia.org",
            f"Search for '{page['title']}' using the search input box.",
        ]

        subheading = None
        if level == 2:
            steps.append(
                f"Once on the page titled '{page['title']}', go to section on '{heading}'"
            )
        elif level == 3:
            for i in range(idx, 0, -1):
                if headings[i]["level"] == 2:
                    subheading = heading
                    heading = headings[i]["heading"]
                    break

            steps.append(
                f"Once on the page titled '{page['title']}', go to subsection '{subheading}' within section '{heading}'"
            )

        tasks.append(
            dict(
                task_type="wikipedia_goto_section",
                keyword=keyword,
                all_headings=headings,
                heading=heading,
                subheading=subheading,
                page=page,
                steps=steps,
            )
        )

    return tasks


def get_wikipedia_qa_generator():
    class QuestionAnswer(BaseModel):
        question: str = Field(
            description="Factual question that can be answered based on the provided context."
        )
        answer: str = Field(
            description="Answer to the question typically containing 1-5 words or at most 20 words."
        )

    @ell.complex(model="gpt-4o", response_format=QuestionAnswer)
    def lmp(
        persona: str,
        keyword: str,
        title: str,
        section: str,
        section_content: str,
    ):
        return [
            ell.system(f"You are {persona}"),
            ell.user(
                f"Generate a factual question answer pair of relevance to you based on the following context drawn from '{section}' section of the wikipedia article titled '{title}' found for your search query '{keyword}':\n\n{section_content}\n\n## Guidelines\n\n- Question should be such that the answer typically contains 1-5 words or at most 20 words. Make sure you question is related to the search query or keyword and can be answered purely based on the context without requiring any other world knowledge."
            ),
        ]

    def get_wikipedia_qa_from_llm(
        persona: str,
        keyword: str,
        title: str,
        section: str,
        section_content: str,
    ) -> tuple[str, str]:
        qa: QuestionAnswer = lmp(persona, keyword, title, section, section_content).parsed  # type: ignore
        return qa.question, qa.answer

    return get_wikipedia_qa_from_llm


def create_wikipedia_qa_task(
    keyword: str, persona: str, num_tasks: int, from_intro: bool = False
):
    page_and_content = wikipedia_api.get_first_page_content(keyword)
    if page_and_content is None:
        return []

    page = page_and_content["page"]
    page_content = page_and_content["content"]
    headings = wikipedia_api.extract_headings_and_content_from_markdown(
        page_content
    )

    tasks = []
    for i in range(num_tasks):
        if from_intro:
            idx = 0
        else:
            idx = random.choice(range(0, len(headings)))
        level = headings[idx]["level"]
        heading = headings[idx]["heading"] if level != 0 else "introduction"
        section_content = headings[idx]["content"]

        steps = [
            "Unless already on a wikipedia page with the search bar visible, go to https://en.wikipedia.org",
            f"Search for '{page['title']}' using the search input box",
        ]

        subheading = None
        if level == 0:
            steps.append(
                f"Once on the page titled '{page['title']}', stay on the introductory section."
            )
        if level == 2:
            steps.append(
                f"Once on the page titled '{page['title']}', go to section on '{heading}'"
            )
        elif level == 3:
            for i in range(idx - 1, 0, -1):
                if headings[i]["level"] == 2:
                    subheading = heading
                    heading = headings[i]["heading"]
                    break

            steps.append(
                f"Once on the page titled '{page['title']}', go to subsection '{subheading}' within section '{heading}'"
            )

        get_wikipedia_qa_from_llm = get_wikipedia_qa_generator()
        question, answer = get_wikipedia_qa_from_llm(
            persona=persona,
            keyword=keyword,
            title=page["title"],
            section=(
                heading if subheading is None else f"{heading} > {subheading}"
            ),
            section_content=section_content,
        )
        steps.append(
            f"Now scroll down through the section until you have found the answer to the question '{question}'. When you find the answer, convey it to the user."
        )
        tasks.append(
            dict(
                task_type="wikipedia_qa",
                keyword=keyword,
                heading=heading,
                subheading=subheading,
                page=page,
                section_content=section_content,
                question=question,
                answer=answer,
                steps=steps,
            )
        )

    return tasks


def generate_wikipedia_task(
    persona: str,
    task_type: Literal[
        "wikipedia_basic_search", "wikipedia_goto_section", "wikipedia_qa"
    ],
    num_keywords: int,
    tasks_per_keyword: int = 1,
    keywords: Optional[list[str]] = None,
):
    if task_type == "wikipedia_basic_search":
        assert (
            tasks_per_keyword == 1
        ), f"wikipedia_basic_search only supports tasks_per_keyword==1 but got {tasks_per_keyword}"

    if keywords is None:
        keywords = get_wikipedia_keywords_generator()(
            persona=persona, num_keywords=num_keywords
        )

    tasks = []
    for keyword in keywords:
        if task_type == "wikipedia_basic_search":
            tasks.extend(create_wikipedia_basic_search_task(keyword))
        elif task_type == "wikipedia_goto_section":
            tasks.extend(
                create_wikipedia_goto_section_task(keyword, tasks_per_keyword)
            )
        elif task_type == "wikipedia_qa":
            tasks.extend(
                create_wikipedia_qa_task(keyword, persona, tasks_per_keyword)
            )

    for task in tasks:
        task["instruction"] = get_instruction(
            "wikipedia", task["steps"]
        ).model_dump()
    return dict(tasks=tasks, keywords=keywords)


WIKIPEDIA_TASK_TYPES = [
    "wikipedia_basic_search",
    "wikipedia_goto_section",
    "wikipedia_qa",
]


if __name__ == "__main__":
    tasks = generate_wikipedia_task(
        persona="A computer scientist.",
        task_type="wikipedia_goto_section",
        num_keywords=1,
        tasks_per_keyword=1,
    )
    import ipdb

    ipdb.set_trace()
